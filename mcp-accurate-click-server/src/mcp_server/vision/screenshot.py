"""
Screenshot capture utilities with graceful dependency handling.

This module provides screenshot capture capabilities with optional dependencies.
Falls back gracefully if computer vision libraries are not installed.
"""

import io
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np

from .models import BoundingBox

logger = logging.getLogger(__name__)

# Optional dependencies with graceful degradation
try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageGrab = None
    logger.warning("Pillow not available. Screenshot functionality will be limited.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None  # Placeholder
    logger.warning("OpenCV not available. Advanced image processing disabled.")

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    mss = None
    logger.info("mss not available. Using PIL for screenshots.")


class ScreenshotError(Exception):
    """Exception raised for screenshot capture errors."""
    pass


class ScreenCapture:
    """
    Screenshot capture utilities with multiple backend support.

    Supports PIL (ImageGrab), mss, and OpenCV for flexibility and performance.
    """

    def __init__(self, backend: str = 'auto'):
        """
        Initialize screenshot capture.

        Args:
            backend: Screenshot backend ('auto', 'pil', 'mss')
        """
        self.backend = self._select_backend(backend)
        self._mss_instance = None

    def _select_backend(self, backend: str) -> str:
        """Select best available backend."""
        if backend == 'auto':
            if MSS_AVAILABLE:
                return 'mss'
            elif PIL_AVAILABLE:
                return 'pil'
            else:
                raise ScreenshotError("No screenshot backend available. Install Pillow or mss.")

        if backend == 'mss' and not MSS_AVAILABLE:
            raise ScreenshotError("mss backend requested but not available.")
        if backend == 'pil' and not PIL_AVAILABLE:
            raise ScreenshotError("PIL backend requested but not available.")

        return backend

    def capture_region(
        self,
        bbox: BoundingBox,
        as_numpy: bool = True
    ) -> Union[np.ndarray, 'Image.Image']:
        """
        Capture screenshot of specific region.

        Args:
            bbox: Bounding box to capture
            as_numpy: Return as numpy array (BGR) instead of PIL Image

        Returns:
            Screenshot as numpy array or PIL Image

        Raises:
            ScreenshotError: If capture fails
        """
        try:
            if self.backend == 'mss':
                return self._capture_region_mss(bbox, as_numpy)
            else:
                return self._capture_region_pil(bbox, as_numpy)
        except Exception as e:
            raise ScreenshotError(f"Failed to capture region: {e}")

    def _capture_region_pil(
        self,
        bbox: BoundingBox,
        as_numpy: bool
    ) -> Union[np.ndarray, 'Image.Image']:
        """Capture region using PIL."""
        if not PIL_AVAILABLE:
            raise ScreenshotError("PIL not available")

        screenshot = ImageGrab.grab(bbox=(bbox.x, bbox.y, bbox.x2, bbox.y2))

        if as_numpy:
            if CV2_AVAILABLE:
                return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            else:
                return np.array(screenshot)

        return screenshot

    def _capture_region_mss(
        self,
        bbox: BoundingBox,
        as_numpy: bool
    ) -> Union[np.ndarray, 'Image.Image']:
        """Capture region using mss (faster)."""
        if not MSS_AVAILABLE:
            raise ScreenshotError("mss not available")

        if self._mss_instance is None:
            self._mss_instance = mss.mss()

        monitor = {
            'left': bbox.x,
            'top': bbox.y,
            'width': bbox.width,
            'height': bbox.height
        }

        screenshot = self._mss_instance.grab(monitor)

        if as_numpy:
            # mss returns BGRA, convert to BGR
            img_array = np.array(screenshot)
            if CV2_AVAILABLE:
                return cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            else:
                return img_array[:, :, :3]  # Remove alpha channel

        # Convert to PIL Image
        if PIL_AVAILABLE:
            return Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        else:
            raise ScreenshotError("PIL required to return Image object")

    def capture_full_screen(
        self,
        monitor: int = 0,
        as_numpy: bool = True
    ) -> Union[np.ndarray, 'Image.Image']:
        """
        Capture full screen screenshot.

        Args:
            monitor: Monitor number (0 for primary)
            as_numpy: Return as numpy array (BGR) instead of PIL Image

        Returns:
            Screenshot as numpy array or PIL Image

        Raises:
            ScreenshotError: If capture fails
        """
        try:
            if self.backend == 'mss':
                return self._capture_full_mss(monitor, as_numpy)
            else:
                return self._capture_full_pil(as_numpy)
        except Exception as e:
            raise ScreenshotError(f"Failed to capture screen: {e}")

    def _capture_full_pil(self, as_numpy: bool) -> Union[np.ndarray, 'Image.Image']:
        """Capture full screen using PIL."""
        if not PIL_AVAILABLE:
            raise ScreenshotError("PIL not available")

        screenshot = ImageGrab.grab()

        if as_numpy:
            if CV2_AVAILABLE:
                return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            else:
                return np.array(screenshot)

        return screenshot

    def _capture_full_mss(
        self,
        monitor: int,
        as_numpy: bool
    ) -> Union[np.ndarray, 'Image.Image']:
        """Capture full screen using mss."""
        if not MSS_AVAILABLE:
            raise ScreenshotError("mss not available")

        if self._mss_instance is None:
            self._mss_instance = mss.mss()

        # monitor 0 is all monitors, 1 is primary, etc.
        screenshot = self._mss_instance.grab(self._mss_instance.monitors[monitor + 1])

        if as_numpy:
            img_array = np.array(screenshot)
            if CV2_AVAILABLE:
                return cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            else:
                return img_array[:, :, :3]

        if PIL_AVAILABLE:
            return Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        else:
            raise ScreenshotError("PIL required to return Image object")

    def save_screenshot(
        self,
        image: Union[np.ndarray, 'Image.Image'],
        path: Union[str, Path]
    ) -> None:
        """
        Save screenshot to file.

        Args:
            image: Screenshot as numpy array or PIL Image
            path: Output file path

        Raises:
            ScreenshotError: If save fails
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(image, np.ndarray):
                if CV2_AVAILABLE:
                    cv2.imwrite(str(path), image)
                elif PIL_AVAILABLE:
                    # Convert numpy to PIL
                    pil_image = Image.fromarray(image)
                    pil_image.save(str(path))
                else:
                    raise ScreenshotError("No image library available to save")
            else:
                # PIL Image
                image.save(str(path))

            logger.debug(f"Screenshot saved to {path}")

        except Exception as e:
            raise ScreenshotError(f"Failed to save screenshot: {e}")

    def load_image(
        self,
        path: Union[str, Path],
        as_numpy: bool = True
    ) -> Union[np.ndarray, 'Image.Image']:
        """
        Load image from file.

        Args:
            path: Image file path
            as_numpy: Return as numpy array (BGR) instead of PIL Image

        Returns:
            Image as numpy array or PIL Image

        Raises:
            ScreenshotError: If load fails
        """
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {path}")

            if as_numpy and CV2_AVAILABLE:
                return cv2.imread(str(path))
            elif PIL_AVAILABLE:
                img = Image.open(path)
                if as_numpy:
                    if CV2_AVAILABLE:
                        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    else:
                        return np.array(img)
                return img
            else:
                raise ScreenshotError("No image library available")

        except Exception as e:
            raise ScreenshotError(f"Failed to load image: {e}")

    def crop_image(
        self,
        image: Union[np.ndarray, 'Image.Image'],
        bbox: BoundingBox
    ) -> Union[np.ndarray, 'Image.Image']:
        """
        Crop region from image.

        Args:
            image: Source image
            bbox: Region to crop

        Returns:
            Cropped image in same format as input
        """
        if isinstance(image, np.ndarray):
            return image[bbox.y:bbox.y2, bbox.x:bbox.x2]
        else:
            return image.crop((bbox.x, bbox.y, bbox.x2, bbox.y2))

    def resize_image(
        self,
        image: Union[np.ndarray, 'Image.Image'],
        width: int,
        height: int
    ) -> Union[np.ndarray, 'Image.Image']:
        """
        Resize image.

        Args:
            image: Source image
            width: Target width
            height: Target height

        Returns:
            Resized image in same format as input
        """
        if isinstance(image, np.ndarray):
            if CV2_AVAILABLE:
                return cv2.resize(image, (width, height))
            elif PIL_AVAILABLE:
                pil_image = Image.fromarray(image)
                resized = pil_image.resize((width, height))
                return np.array(resized)
            else:
                raise ScreenshotError("No resize capability available")
        else:
            return image.resize((width, height))

    def to_grayscale(
        self,
        image: Union[np.ndarray, 'Image.Image']
    ) -> Union[np.ndarray, 'Image.Image']:
        """
        Convert image to grayscale.

        Args:
            image: Source image

        Returns:
            Grayscale image in same format as input
        """
        if isinstance(image, np.ndarray):
            if CV2_AVAILABLE:
                if len(image.shape) == 3:
                    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                return image
            elif PIL_AVAILABLE:
                pil_image = Image.fromarray(image)
                gray = pil_image.convert('L')
                return np.array(gray)
            else:
                raise ScreenshotError("No grayscale conversion available")
        else:
            return image.convert('L')

    def __del__(self):
        """Cleanup resources."""
        if self._mss_instance:
            self._mss_instance.close()


# Global instance for convenience
_default_capture = None


def get_screen_capture() -> ScreenCapture:
    """Get default ScreenCapture instance."""
    global _default_capture
    if _default_capture is None:
        _default_capture = ScreenCapture()
    return _default_capture


# Convenience functions
def capture_region(bbox: BoundingBox, as_numpy: bool = True) -> Union[np.ndarray, 'Image.Image']:
    """Capture screenshot region using default instance."""
    return get_screen_capture().capture_region(bbox, as_numpy)


def capture_screen(monitor: int = 0, as_numpy: bool = True) -> Union[np.ndarray, 'Image.Image']:
    """Capture full screen using default instance."""
    return get_screen_capture().capture_full_screen(monitor, as_numpy)


def save_screenshot(image: Union[np.ndarray, 'Image.Image'], path: Union[str, Path]) -> None:
    """Save screenshot using default instance."""
    return get_screen_capture().save_screenshot(image, path)


def load_image(path: Union[str, Path], as_numpy: bool = True) -> Union[np.ndarray, 'Image.Image']:
    """Load image using default instance."""
    return get_screen_capture().load_image(path, as_numpy)
