from abc import ABC, abstractmethod


class ROIExtractor(ABC):
    @abstractmethod
    def extract(self, input_image):
        """Return (cropped, cropped_ext, boundingboxed_image) or (None, None, None) on failure."""
        raise NotImplementedError
