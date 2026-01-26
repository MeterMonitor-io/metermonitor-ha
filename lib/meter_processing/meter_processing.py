import base64
import gc
import os
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
import onnxruntime as ort


class MeterPredictor:
    """
    A class to perform water meter digit detection (using YOLO with OBB)
    and digit classification
    """

    def __init__(self):
        """
        Initializes the ONNX inference sessions for YOLO and digit classifier.
        Optimized for minimal memory usage - uses ~70% less RAM than TensorFlow+PyTorch.
        """
        print("[MeterPredictor] Loading ONNX models...")

        # Configure ONNX Runtime for minimal memory usage
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.enable_mem_pattern = False  # Reduce memory fragmentation
        sess_options.enable_cpu_mem_arena = False  # Reduce memory overhead

        # Load YOLO ONNX model for oriented bounding box detection
        self.yolo_session = ort.InferenceSession(
            "models/yolo-best-obb-2.onnx",
            sess_options=sess_options,
            providers=['CPUExecutionProvider']
        )

        # Load digit classifier ONNX model
        self.digit_session = ort.InferenceSession(
            'models/best_model.onnx',
            sess_options=sess_options,
            providers=['CPUExecutionProvider']
        )

        self.class_names = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'r']

        # Get input/output names for both models
        self.yolo_input_name = self.yolo_session.get_inputs()[0].name
        self.yolo_output_names = [output.name for output in self.yolo_session.get_outputs()]

        self.digit_input_name = self.digit_session.get_inputs()[0].name
        self.digit_output_name = self.digit_session.get_outputs()[0].name

        # Force garbage collection after loading models
        gc.collect()
        print("[MeterPredictor] ONNX models loaded successfully with minimal memory footprint.")
        print(f"[MeterPredictor] YOLO input: {self.yolo_input_name}")
        print(f"[MeterPredictor] Digit classifier input: {self.digit_input_name}")

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

        # Rotate the image 180 degrees
        if rotated_180:
            #  is image.py
            input_image = input_image.rotate(180, expand=True)

        print(f"[Predictor] Running YOLO region-of-interest detection...")

        # Prepare image for YOLO ONNX model
        img_np = np.array(input_image)
        original_height, original_width = img_np.shape[:2]

        # Letterbox resizing (maintain aspect ratio)
        target_size = 640
        scale = min(target_size / original_width, target_size / original_height)
        new_w = int(original_width * scale)
        new_h = int(original_height * scale)

        img_resized = cv2.resize(img_np, (new_w, new_h))

        # Create canvas with padding (114 is standard YOLO padding color)
        canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)

        # Center the image
        top = (target_size - new_h) // 2
        left = (target_size - new_w) // 2
        canvas[top:top+new_h, left:left+new_w] = img_resized

        # Normalize and prepare for ONNX (CHW format)
        img_normalized = canvas.astype(np.float32) / 255.0
        img_transposed = img_normalized.transpose(2, 0, 1)  # HWC to CHW
        img_batch = np.expand_dims(img_transposed, axis=0)  # Add batch dimension

        # Run YOLO ONNX inference
        try:
            outputs = self.yolo_session.run(None, {self.yolo_input_name: img_batch})
        except Exception as e:
            print(f"[Predictor] YOLO inference failed: {e}")
            return [], [], None, None

        # YOLO OBB output format:
        # outputs[0] shape is typically [batch, num_preds, num_values]
        # For OBB: [batch, num_preds, 7+num_classes] where 7 = [x, y, w, h, rotation, confidence, class_id]
        # OR [batch, features, anchors] e.g. [1, 6, 8400]

        output = outputs[0]

        # Transpose if features are in the second dimension (channels first)
        # e.g. [1, 6, 8400] -> [1, 8400, 6]
        if output.shape[1] < output.shape[2]:
            output = output.transpose(0, 2, 1)

        predictions = output[0]  # Remove batch dimension

        # Filter by confidence
        # For OBB with 1 class, we expect 6 features.
        # The order varies by version. It could be [x, y, w, h, rotation, confidence] or [x, y, w, h, confidence, rotation]

        # Heuristic to determine which channel is confidence and which is rotation
        # Confidence is strictly [0, 1]. Rotation is in radians (approx -1.57 to 1.57) and can be > 1.

        if predictions.shape[1] == 6:
            col4 = predictions[:, 4]
            col5 = predictions[:, 5]

            max4 = np.max(col4)
            max5 = np.max(col5)

            # If one column has values > 1.0, it must be rotation
            if max5 > 1.05:
                confidence_idx = 4
                rotation_idx = 5
                print(f"[Predictor] Detected format: [x, y, w, h, conf, rot] (max col5={max5:.2f})")
            elif max4 > 1.05:
                confidence_idx = 5
                rotation_idx = 4
                print(f"[Predictor] Detected format: [x, y, w, h, rot, conf] (max col4={max4:.2f})")
            else:
                # Ambiguous if both are small.
                # Default to index 4 as confidence (common in newer versions: xywh + conf + rot)
                confidence_idx = 4
                rotation_idx = 5
                print(f"[Predictor] Ambiguous format (max values <= 1.0). Defaulting to [x, y, w, h, conf, rot]")

        elif predictions.shape[1] >= 7:
             # [x, y, w, h, conf, class..., rot] or similar
             # Usually rotation is the last one or after coords
             # Let's assume standard YOLOv8/11 OBB: [x, y, w, h, split_conf?, rot?]
             # Actually, often it is [x, y, w, h, class_probs..., rot]
             # If 1 class: [x, y, w, h, class_prob, rot] -> same as 6 channels

             # If we have 7 channels, maybe 2 classes?
             # [x, y, w, h, class1, class2, rot]

             # Rotation is likely the last channel or the one with values > 1

             # Find channel with max > 1.05
             rotation_idx = -1
             for i in range(4, predictions.shape[1]):
                 if np.max(predictions[:, i]) > 1.05:
                     rotation_idx = i
                     break

             if rotation_idx != -1:
                 # If we found rotation, the rest are classes/confidence
                 # Take max of other channels as confidence
                 class_indices = [i for i in range(4, predictions.shape[1]) if i != rotation_idx]
                 confidence_idx = class_indices[0] # Just for scalar indexing if needed
                 # But we should take max over class indices
             else:
                 # Fallback
                 rotation_idx = predictions.shape[1] - 1
                 confidence_idx = 4

        if predictions.shape[1] >= 6:
            if predictions.shape[1] > 6:
                # Multiple classes or class probs, take max of all class columns
                # Exclude rotation index
                class_cols = [i for i in range(4, predictions.shape[1]) if i != rotation_idx]
                if class_cols:
                    confidences = np.max(predictions[:, class_cols], axis=1)
                else:
                    confidences = predictions[:, confidence_idx]
            else:
                confidences = predictions[:, confidence_idx]
        else:
             confidences = predictions[:, confidence_idx]

        valid_mask = confidences > 0.15

        if not np.any(valid_mask):
            print(f"[Predictor] No instances detected with confidence > 0.15")
            return [], [], None, None

        valid_predictions = predictions[valid_mask]
        valid_confidences = confidences[valid_mask]

        # Get the detection with highest confidence
        best_idx = np.argmax(valid_confidences)
        detection = valid_predictions[best_idx]

        print(f"[Predictor] Raw detection: {detection}")
        print(f"[Predictor] Confidence: {valid_confidences[best_idx]:.4f}")
        print(f"[Predictor] Rotation: {detection[rotation_idx]:.4f}")
        print(f"[Predictor] Original size: {original_width}x{original_height}")

        # Extract OBB parameters (x_center, y_center, width, height, rotation)
        x_center_norm = detection[0]
        y_center_norm = detection[1]
        width_norm = detection[2]
        height_norm = detection[3]

        # Handle rotation angle
        rotation = detection[rotation_idx]  # In radians

        # Scale back to original image size
        # Check if coordinates are normalized (0-1) or pixels (0-640)
        if x_center_norm < 2.0 and y_center_norm < 2.0 and width_norm < 2.0 and height_norm < 2.0:
             # Normalized coordinates -> convert to pixels in 640x640 space first
             x_center_pixel = x_center_norm * 640.0
             y_center_pixel = y_center_norm * 640.0
             width_pixel = width_norm * 640.0
             height_pixel = height_norm * 640.0
        else:
             # Pixel coordinates
             x_center_pixel = x_center_norm
             y_center_pixel = y_center_norm
             width_pixel = width_norm
             height_pixel = height_norm

        # Adjust for letterboxing
        # 1. Remove padding shift
        x_center_pixel -= left
        y_center_pixel -= top

        # 2. Scale back to original size
        x_center = x_center_pixel / scale
        y_center = y_center_pixel / scale
        width = width_pixel / scale
        height = height_pixel / scale

        # Convert OBB (center, size, rotation) to 4 corner points
        # Create corner offsets (unrotated box)
        hw = width / 2.0
        hh = height / 2.0

        corners_unrotated = np.array([
            [-hw, -hh],  # top-left
            [hw, -hh],   # top-right
            [hw, hh],    # bottom-right
            [-hw, hh]    # bottom-left
        ], dtype=np.float32)

        # Apply rotation
        cos_r = np.cos(rotation)
        sin_r = np.sin(rotation)
        rotation_matrix = np.array([
            [cos_r, -sin_r],
            [sin_r, cos_r]
        ], dtype=np.float32)

        corners_rotated = corners_unrotated @ rotation_matrix.T

        # Translate to center position
        obb_coords = corners_rotated + np.array([x_center, y_center], dtype=np.float32)

        img = img_np

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

        # export base64 with the input_image + the inserted bounding box for debugging
        img_with_bbox = np.array(input_image)
        boundingboxed_image = None
        if obb_coords is not None:
            obb_points = obb_coords.reshape(4, 2).astype(np.int32)
            cv2.polylines(img_with_bbox, [obb_points], isClosed=True, color=(255, 0, 0), thickness=2)

            pil_img = Image.fromarray(img_with_bbox)
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue())
            # to string
            boundingboxed_image = img_str.decode('utf-8')

        return base64s, digits, target_brightness, boundingboxed_image

    def apply_threshold(self, digit, threshold_low, threshold_high, islanding_padding=40, invert=False):
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
        if invert:
            pil_img = Image.fromarray(255 - img_uint8)  # Invert for
        pil_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return img_str, img_norm

    # use the classifier to predict the digit, returns the top 3 predictions with their confidence
    def predict_digit(self, digit):
        # Perform prediction using ONNX model
        predictions = self.digit_session.run(
            [self.digit_output_name],
            {self.digit_input_name: digit}
        )[0]

        top3 = np.argsort(predictions[0])[-3:][::-1]
        pairs = [(self.class_names[i], float(predictions[0][i])) for i in top3]

        return pairs

    def predict_digits(self, digits):
        """
        Digits are np arrays
        predict the digits
        """
        # Predict each digit
        predicted_digits = []
        for i,digit in enumerate(digits):
            digit = self.predict_digit(digit)
            predicted_digits.append(digit)

        # Clean up memory after batch prediction
        gc.collect()

        return predicted_digits

    def apply_thresholds(self, digits, thresholds, thresholds_last, islanding_padding):
        """
        Digits are np arrays
        apply black/white thresholding to each digit
        """

        # Apply thresholding
        thresholded_digits = []
        base64s = []
        base64s_inverted = []

        threshold_low = thresholds[0]
        threshold_high = thresholds[1]
        for i, digit in enumerate(digits):
            if i >= len(digits) - 3:
                threshold_low = thresholds_last[0]
                threshold_high = thresholds_last[1]
            img_str, digit = self.apply_threshold(digit, threshold_low, threshold_high, islanding_padding)

            thresholded_digits.append(digit)
            base64s.append(img_str)

            # also store inverted images as base64 for debugging
            img_uint8 = (digit.squeeze() * 255).astype(np.uint8)
            pil_img = Image.fromarray(255 - img_uint8)  # Invert for
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            img_str_inverted = base64.b64encode(buffered.getvalue()).decode('utf-8')
            base64s_inverted.append(img_str_inverted)

        return base64s, thresholded_digits, base64s_inverted