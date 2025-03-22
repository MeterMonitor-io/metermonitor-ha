import base64
import os
import random
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from tensorflow.keras.models import load_model

class MeterPredictor:
    """
    A class to perform water meter digit detection (using YOLO with OBB)
    and digit classification
    """

    def __init__(self):
        """
        Initializes the YOLO model and loads the keras model, so they can
        be reused for multiple images without re-initializing.
        """
        # Load YOLO model (oriented bounding box capable)
        self.model = YOLO("models/yolo-best-obb-2.pt")

        # Define the model architecture (same as during training)
        self.digitmodel = load_model('models/th_digit_classifier_2.h5')
        self.class_names = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'r']

    def extract_display_and_segment(self, input_image, segments=7, rotated_180=False, extended_last_digit=False, shrink_last_3=False, target_brightness=None):
        """
        Predicts the water meter reading on a single image:
          - Runs YOLO detection for oriented bounding box (OBB)
          - Applies perspective transform to 'straighten' the meter
          - Splits the meter into vertical segments

        Args:
            input_image (PIL.Image): The input image to process.
            segments (int): The number of segments to split the meter into.
            rotated_180 (bool): Whether to rotate the meter 180 degrees.
            extended_last_digit (bool): Whether to extend the last digit for better classification.
            shrink_last_3 (bool): Whether to shrink the last 3 digits for better classification.
            target_brightness (float): The target brightness to adjust the image to.
        """

        # run yolo detection
        results = self.model.predict(input_image, save=False)
        obb_data = results[0].obb

        # If no OBB found, bail out
        if (
                obb_data is None or
                obb_data.xyxyxyxy is None or
                len(obb_data.xyxyxyxy) == 0
        ):
            print(f"[INFO] No instances detected in the image.")
            [],[]

        # We'll use the first detected bounding box

        if len(obb_data.xyxyxyxy) == 0:
            print ("No bounding box found")
            return [],[], None

        obb_coords = obb_data.xyxyxyxy[0].cpu().numpy()
        img = np.array(input_image)

        # 1. Cut out the detected OBB

        # Reshape OBB coordinates into four (x,y) points
        points = obb_coords.reshape(4, 2).astype(np.float32)
        # Sort the points by y-coordinate (top to bottom)
        points = sorted(points, key=lambda x: x[1])
        # Separate top-left, top-right vs bottom-left, bottom-right
        if points[0][0] < points[1][0]:
            top_left, top_right = points[0], points[1]
        else:
            top_left, top_right = points[1], points[0]

        if points[2][0] < points[3][0]:
            bottom_left, bottom_right = points[2], points[3]
        else:
            bottom_left, bottom_right = points[3], points[2]

        # Reassemble into final order: [top-left, top-right, bottom-right, bottom-left]
        points = np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")

        # Compute bounding box width/height
        width_a = np.linalg.norm(points[0] - points[1])
        width_b = np.linalg.norm(points[2] - points[3])
        max_width = max(int(width_a), int(width_b))

        height_a = np.linalg.norm(points[1] - points[2])
        height_b = np.linalg.norm(points[3] - points[0])
        max_height = max(int(height_a), int(height_b))

        # Perspective transform to get the "front-facing" rectangle
        dst_points = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(points, dst_points)
        rotated_cropped_img = cv2.warpPerspective(img, M, (max_width, max_height))
        rotated_cropped_img_ext = None

        # Cut out a larger area for the last digit
        if extended_last_digit:
            rotated_cropped_img_ext = cv2.warpPerspective(img, M, (max_width, int(max_height * 1.2)))

        # Rotate the image 180 degrees if needed
        if rotated_180:
            rotated_cropped_img = cv2.rotate(rotated_cropped_img, cv2.ROTATE_180)
            if extended_last_digit:
                rotated_cropped_img_ext = cv2.rotate(rotated_cropped_img_ext, cv2.ROTATE_180)

        # Split the cropped meter into segments vertical parts for classification
        if (segments == 0): return [],[]
        part_width = rotated_cropped_img.shape[1] // segments

        base64s = []
        digits = []

        last_x = 0

        # cut out the segments
        for i in range(segments):
            if shrink_last_3 and i >= segments - 3:
                t_part_width = int(part_width * 0.8)
            elif shrink_last_3:
                t_part_width = int(((part_width * segments) - (3 * part_width * 0.8)) / (segments - 3))
            else:
                t_part_width = part_width

            # Extract segment from last_x to last_x + t_part_width
            part = rotated_cropped_img[:, last_x: last_x + t_part_width]

            if extended_last_digit and i == segments - 1:
                part = rotated_cropped_img_ext[:, last_x: last_x + t_part_width]
            last_x = last_x + t_part_width

            # Convert segment to base64 string for storage
            digits.append(part)

        # Adjust brightness of each image
        mean_brightnesses = [np.mean(img) for img in digits]
        adjusted_images = []
        if target_brightness is None:
            target_brightness = np.mean(mean_brightnesses)
        for img, mean_brightness in zip(digits, mean_brightnesses):
            adjustment_factor = target_brightness / mean_brightness
            adjusted_img = np.clip(img * adjustment_factor, 0, 255).astype(np.uint8)
            adjusted_images.append(adjusted_img)

        digits = adjusted_images

        # Convert to base64 for temporary storage
        for part in digits:
            pil_img = Image.fromarray(part)

            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue())
            # to string
            img_str = img_str.decode('utf-8')

            base64s.append(img_str)

        return base64s, digits, target_brightness

    def apply_threshold(self, digit, threshold_low, threshold_high, islanding_padding=40):
        threshold_low, threshold_high = int(threshold_low), int(threshold_high)
        islanding_padding = int(islanding_padding)

        # Convert the digit image to grayscale.
        digit = cv2.cvtColor(digit, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to get a binary image.
        digit = cv2.inRange(digit, threshold_low, threshold_high)

        # Find connected regions, by default the background needs to be black (0) and the digits white (255).
        # Invert the image to match this requirement.
        inverted = cv2.bitwise_not(digit)

        # Find connected components (8-connectivity by default)
        num_labels, labels = cv2.connectedComponents(inverted)

        # Create a BGR color image with white background
        color_image = np.full((*digit.shape, 3), (255, 255, 255), dtype=np.uint8)

        # Get the dimensions of the image
        height, width = digit.shape

        # Calculate the middle x% region (with islanding_padding% padding on all sides)
        start_x = int((islanding_padding / 100.0) * width)
        end_x = int(1.0 - (islanding_padding / 100.0)  * width)
        start_y = int((islanding_padding / 100.0) * height)
        end_y = int(1.0 - (islanding_padding / 100.0) * height)

        extracted = 0
        extracted_percentage = 0
        for label in range(1, num_labels):
            # Slice the labels to the middle region and check for any occurrence of the current label
            component_region = labels[start_y:end_y, start_x:end_x]
            in_middle = np.any(component_region == label)

            if in_middle:
                color = (0, 0, 0)
                extracted += 1

                # Calculate the percentage of the component in the middle region
                component_area = np.sum(labels == label)
                total_area = height * width
                extracted_percentage += component_area / total_area * 100
            else:
                # remove the component if it is not in the middle region
                color = (255, 255, 255)

            color_image[labels == label] = color

        # if no components are in the middle region or less than 10% of the image is extracted, use the whole image
        if extracted == 0 or extracted_percentage < 10:
            # use the whole image
            color_image = np.full((*digit.shape, 3), (255, 255, 255), dtype=np.uint8)
            color_image[labels != 0] = (0, 0, 0)

        # back to greyscale
        color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        digit = cv2.resize(color_image, (40, 64))

        # --- Normalize & add extra dimensions ---
        img_norm = digit.astype('float32') / 255.0
        img_norm = np.expand_dims(img_norm, axis=-1)  # add channel dimension
        img_norm = np.expand_dims(img_norm, axis=0)  # add batch dimension

        img_uint8 = (img_norm.squeeze() * 255).astype(np.uint8)  # Remove extra dims & convert to uint8
        pil_img = Image.fromarray(img_uint8)

        # Encode image to Base64
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return img_str, img_norm

    # use the classifier to predict the digit, returns the top 3 predictions with their confidence
    def predict_digit(self, digit):
        # Perform prediction using your model
        predictions = self.digitmodel.predict(digit)
        top3 = np.argsort(predictions[0])[-3:][::-1]
        pairs = [(self.class_names[i], float(predictions[0][i])) for i in top3]

        # the second element of the pair is used to provide predictions from a second model for testing purposes
        return pairs, []

    def predict_digits(self, digits):
        """
        Digits are np arrays
        predict the digits
        """

        # Predict each digit
        predicted_digits = []
        second_model_digits = []
        for i,digit in enumerate(digits):
            digit, tess_digit = self.predict_digit(digit)
            predicted_digits.append(digit)
            second_model_digits.append(tess_digit)

        return predicted_digits, second_model_digits

    def apply_thresholds(self, digits, thresholds, thresholds_last, islanding_padding):
        """
        Digits are np arrays
        apply black/white thresholding to each digit
        """

        # Apply thresholding
        thresholded_digits = []
        base64s = []

        threshold_low = thresholds[0]
        threshold_high = thresholds[1]
        for i, digit in enumerate(digits):
            if i >= len(digits) - 3:
                threshold_low = thresholds_last[0]
                threshold_high = thresholds_last[1]
            img_str, digit = self.apply_threshold(digit, threshold_low, threshold_high, islanding_padding)

            thresholded_digits.append(digit)
            base64s.append(img_str)

        return base64s, thresholded_digits