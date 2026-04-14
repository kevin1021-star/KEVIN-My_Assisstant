import pyautogui
import logging
from typing import Optional

logger = logging.getLogger("KEVIN-GESTURE")

# Disable pyautogui failsafe for smooth edge movement (Careful: User can still use physical mouse to override)
pyautogui.FAILSAFE = True

class GestureService:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.last_y: Optional[float] = None
        self.last_x: Optional[float] = None
        self.scroll_threshold = 0.02
        self.min_delta = 0.002 # Ignore tiny movements to stop jitter

    def process_mouse_sync(self, x: float, y: float, click: bool):
        """Processes mouse movement with low smoothing for a snappy feel."""
        try:
            # Check for Jitter/Stillness
            if self.last_x is not None:
                if abs(x - self.last_x) < self.min_delta and abs(y - self.last_y) < self.min_delta and not click:
                    return

            # Invert X for mirror feel
            screen_x = int((1 - x) * self.screen_width)
            screen_y = int(y * self.screen_height)

            # Scroll 
            if self.last_y is not None:
                dy = y - self.last_y
                if abs(dy) > self.scroll_threshold:
                    pyautogui.scroll(-int(dy * 400))
            
            self.last_x, self.last_y = x, y

            # Move Mouse (Instant for snappy feel)
            pyautogui.moveTo(screen_x, screen_y, _pause=False)

            if click:
                pyautogui.click()

        except Exception as e:
            logger.error(f"Gesture error: {e}")

    def reset(self):
        """Resets state when tracking is lost."""
        self.last_y = None
