from abc import ABC, abstractmethod
import base64
import json
import numpy as np
import cv2


class ROIExtractor(ABC):
    @abstractmethod
    def extract(self, input_image):
        """Return (cropped, cropped_ext, boundingboxed_image) or (None, None, None) on failure."""
        raise NotImplementedError


class ROIExtractorTemplated(ROIExtractor):
    """
    Abstract base class for template-based ROI extractors.

    Handles serialization/deserialization of reference images and precomputed data.
    Subclasses must implement feature extraction and matching logic.
    """

    def __init__(self, reference_image, config_dict):
        """
        Initialize templated extractor.

        Args:
            reference_image: Reference image (numpy array)
            config_dict: Configuration dictionary (will be stored as JSON in DB)
        """
        self.reference_image = reference_image
        self.config = config_dict

        # Convert to grayscale if needed
        if len(reference_image.shape) == 3:
            self.reference_gray = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
        else:
            self.reference_gray = reference_image

    @abstractmethod
    def compute_precomputed_data(self):
        """
        Compute and return precomputed data for caching (e.g., features, masks).

        Returns:
            dict: Dictionary with precomputed data (will be serialized to base64)
        """
        raise NotImplementedError

    @abstractmethod
    def load_precomputed_data(self, precomputed_dict):
        """
        Load precomputed data from cache.

        Args:
            precomputed_dict: Dictionary with precomputed data (deserialized from base64)
        """
        raise NotImplementedError

    def serialize_template(self):
        """
        Serialize template to database format.

        Returns:
            tuple: (reference_image_base64, config_json, precomputed_data_base64)
        """
        # Encode reference image
        _, buffer = cv2.imencode('.jpg', self.reference_image)
        ref_img_b64 = base64.b64encode(buffer).decode('utf-8')

        # Config to JSON
        config_json = json.dumps(self.config)

        # Compute and encode precomputed data
        precomputed = self.compute_precomputed_data()
        precomputed_json = json.dumps(precomputed, cls=NumpyEncoder)
        precomputed_b64 = base64.b64encode(precomputed_json.encode('utf-8')).decode('utf-8')

        return ref_img_b64, config_json, precomputed_b64

    @classmethod
    def deserialize_template(cls, reference_image_base64, config_json, precomputed_data_base64=None):
        """
        Deserialize template from database format.

        Args:
            reference_image_base64: Base64 encoded reference image
            config_json: JSON string with configuration
            precomputed_data_base64: Optional base64 encoded precomputed data

        Returns:
            Instance of the extractor class
        """
        # Decode reference image
        img_bytes = base64.b64decode(reference_image_base64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        reference_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Parse config
        config_dict = json.loads(config_json)

        # Create instance
        instance = cls(reference_image, config_dict)

        # Load precomputed data if available
        if precomputed_data_base64:
            precomputed_json = base64.b64decode(precomputed_data_base64).decode('utf-8')
            precomputed_dict = json.loads(precomputed_json, object_hook=numpy_decoder)
            instance.load_precomputed_data(precomputed_dict)

        return instance


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder for numpy arrays and types."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {
                '__numpy__': True,
                'dtype': str(obj.dtype),
                'shape': obj.shape,
                'data': base64.b64encode(obj.tobytes()).decode('utf-8')
            }
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, cv2.KeyPoint):
            return {
                '__keypoint__': True,
                'pt': obj.pt,
                'size': obj.size,
                'angle': obj.angle,
                'response': obj.response,
                'octave': obj.octave,
                'class_id': obj.class_id
            }
        return super().default(obj)


def numpy_decoder(obj):
    """JSON decoder for numpy arrays and types."""
    if isinstance(obj, dict):
        if obj.get('__numpy__'):
            data = base64.b64decode(obj['data'])
            arr = np.frombuffer(data, dtype=obj['dtype'])
            return arr.reshape(obj['shape'])
        if obj.get('__keypoint__'):
            return cv2.KeyPoint(
                x=obj['pt'][0],
                y=obj['pt'][1],
                size=obj['size'],
                angle=obj['angle'],
                response=obj['response'],
                octave=obj['octave'],
                class_id=obj['class_id']
            )
    return obj
