import importlib
import logging
from typing import Optional

logger = logging.getLogger("KEVIN-GESTURE")

try:
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class GestureService:
    def __init__(self):
        self.pyautogui = self._load_pyautogui()
        self.screen_width, self.screen_height = self.pyautogui.size() if self.pyautogui else (1920, 1080)
        self.last_y: Optional[float] = None
        self.last_x: Optional[float] = None
        self.min_delta = 0.003
        self.is_dragging = False
        self.mouse_down = False

    @staticmethod
    def _load_pyautogui():
        try:
            pyautogui = importlib.import_module("pyautogui")
            pyautogui.FAILSAFE = True
            return pyautogui
        except Exception as exc:
            logger.warning("Gesture mouse control disabled: %s", exc)
            return None

    def process_mouse_sync(
        self,
        x: float,
        y: float,
        click: bool = False,
        right_click: bool = False,
        drag: bool = False,
        scroll_delta: float = 0.0,
    ):
        """Process advanced mouse movement, buttons, and scrolling from hand gestures."""
        if not self.pyautogui:
            return

        try:
            if self.last_x is not None:
                if (
                    abs(x - self.last_x) < self.min_delta
                    and abs(y - self.last_y) < self.min_delta
                    and not click
                    and not right_click
                    and scroll_delta == 0
                    and drag == self.is_dragging
                ):
                    return

            screen_x = int(x * self.screen_width)
            screen_y = int(y * self.screen_height)
            self.last_x, self.last_y = x, y

            if HAS_WIN32:
                win32api.SetCursorPos((screen_x, screen_y))
            else:
                self.pyautogui.moveTo(screen_x, screen_y, _pause=False)

            if scroll_delta:
                if HAS_WIN32:
                    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(scroll_delta), 0)
                else:
                    self.pyautogui.scroll(int(scroll_delta))

            if drag and not self.is_dragging:
                self.pyautogui.mouseDown()
                self.is_dragging = True
            elif not drag and self.is_dragging:
                self.pyautogui.mouseUp()
                self.is_dragging = False

            if click:
                self.pyautogui.click()
            if right_click:
                self.pyautogui.click(button="right")

        except Exception as e:
            logger.error(f"Gesture error: {e}")

    def reset(self):
        """Resets state when tracking is lost."""
        if self.pyautogui and self.is_dragging:
            try:
                self.pyautogui.mouseUp()
            except Exception:
                pass
        self.is_dragging = False
        self.last_y = None
        self.last_x = None
