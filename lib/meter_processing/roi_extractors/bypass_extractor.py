import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from lib.meter_processing.roi_extractors.base import ROIExtractor


class BypassExtractor(ROIExtractor):
    def extract(self, input_image):
        print("[ROIExtractor (Bypass)] Bypassing region-of-interest detection...")
        img_np = np.array(input_image)
        height, width = img_np.shape[:2]

        img_with_bbox = img_np.copy()
        cv2.rectangle(img_with_bbox, (0, 0), (width - 1, height - 1), (255, 0, 0), 2)

        pil_img = Image.fromarray(img_with_bbox)
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        boundingboxed_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return img_np, None, boundingboxed_image
