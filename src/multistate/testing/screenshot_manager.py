"""Screenshot Manager - Handles screenshot capture and storage for testing.

This module provides screenshot management functionality separated from
the main PathTracker to improve modularity and maintainability.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Optional dependencies for screenshot support
try:
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    np = None  # type: ignore
    HAS_CV2 = False


class ScreenshotManager:
    """Manages screenshot capture and storage for test execution tracking.

    This class handles all screenshot-related operations including:
    - Saving screenshots to disk
    - Managing screenshot directory structure
    - Handling optional cv2 dependency

    Thread Safety:
        Individual save operations are atomic. Directory creation uses exist_ok=True.
    """

    def __init__(
        self,
        screenshot_dir: str | Path = "./screenshots",
        enabled: bool = True,
    ) -> None:
        """Initialize ScreenshotManager.

        Args:
            screenshot_dir: Directory for screenshot storage
            enabled: Whether screenshot capture is enabled
        """
        self.screenshot_dir = Path(screenshot_dir)
        self.enabled = enabled and HAS_CV2

        # Warn if screenshots requested but cv2 not available
        if enabled and not HAS_CV2:
            logger.warning(
                "Screenshots requested but opencv-python not available. "
                "Install with: pip install multistate[testing]"
            )

        # Create screenshot directory
        if self.enabled:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Screenshot directory created: {self.screenshot_dir}")

    def save_screenshot(
        self,
        execution_id: str,
        screenshot: Any,
    ) -> str | None:
        """Save a screenshot to disk.

        Args:
            execution_id: Unique identifier for the execution
            screenshot: Screenshot array (numpy ndarray)

        Returns:
            Path to saved screenshot file, or None if save failed/disabled
        """
        if not self.enabled or screenshot is None:
            return None

        if cv2 is None or np is None:
            logger.warning("Cannot save screenshot: cv2/numpy not available")
            return None

        try:
            # Validate screenshot is a numpy array
            if not isinstance(screenshot, np.ndarray):
                logger.warning(
                    f"Screenshot is not a numpy array: {type(screenshot)}. "
                    "Skipping save."
                )
                return None

            # Generate filename
            filename = f"{execution_id}.png"
            filepath = self.screenshot_dir / filename

            # Save screenshot
            success = cv2.imwrite(str(filepath), screenshot)

            if success:
                logger.debug(f"Screenshot saved: {filepath}")
                return str(filepath)
            else:
                logger.error(f"Failed to save screenshot: {filepath}")
                return None

        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return None

    def clear_screenshots(self) -> int:
        """Remove all screenshots from the screenshot directory.

        Returns:
            Number of screenshots deleted
        """
        if not self.screenshot_dir.exists():
            return 0

        count = 0
        for screenshot_file in self.screenshot_dir.glob("*.png"):
            try:
                screenshot_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {screenshot_file}: {e}")

        logger.info(f"Cleared {count} screenshots from {self.screenshot_dir}")
        return count

    @property
    def is_available(self) -> bool:
        """Check if screenshot functionality is available.

        Returns:
            True if cv2 is installed and screenshots are enabled
        """
        return HAS_CV2 and self.enabled
