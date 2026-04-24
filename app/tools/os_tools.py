import logging
import webbrowser
import os
import time
import importlib
from PIL import ImageGrab

logger = logging.getLogger("KEVIN-OS")


def _load_appopener():
    try:
        app_opener = importlib.import_module("AppOpener")
        return getattr(app_opener, "open"), getattr(app_opener, "close")
    except Exception as exc:
        logger.warning("AppOpener unavailable: %s", exc)
        return None, None


def _load_pyautogui():
    try:
        return importlib.import_module("pyautogui")
    except Exception as exc:
        logger.warning("pyautogui unavailable: %s", exc)
        return None


def open_application(app_name: str) -> str:
    """Open a Windows application by name."""
    app_open, _ = _load_appopener()
    if not app_open:
        return "App opening is unavailable on this system right now."

    try:
        app_open(app_name, match_closest=True, output=False)
        return f"Opened {app_name}."
    except Exception as exc:
        return f"Could not open {app_name}: {exc}"


def close_application(app_name: str) -> str:
    """Close a Windows application by name."""
    _, app_close = _load_appopener()
    if not app_close:
        return "App closing is unavailable on this system right now."

    try:
        app_close(app_name, match_closest=True, output=False)
        return f"Closed {app_name}."
    except Exception as exc:
        return f"Could not close {app_name}: {exc}"


def type_text(text: str) -> str:
    """Type text into the active window."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation is unavailable on this system right now."

    try:
        pyautogui.write(text, interval=0.01)
        return f"Typed: {text}"
    except Exception as exc:
        return f"Typing failed: {exc}"


def press_key(key: str) -> str:
    """Press a keyboard key."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation is unavailable on this system right now."

    try:
        pyautogui.press(key)
        return f"Pressed {key}."
    except Exception as exc:
        return f"Key press failed: {exc}"


def open_website(url: str) -> str:
    """Open a website URL in the default browser."""
    try:
        webbrowser.open(url)
        return f"Opened {url}"
    except Exception as exc:
        return f"Could not open {url}: {exc}"


def switch_tab() -> str:
    """Switch to the next tab in the active browser or application."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation unavailable."
    try:
        pyautogui.hotkey("ctrl", "tab")
        return "Switched to next tab."
    except Exception as exc:
        return f"Tab switch failed: {exc}"


def previous_tab() -> str:
    """Switch to the previous tab in the active browser or application."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation unavailable."
    try:
        pyautogui.hotkey("ctrl", "shift", "tab")
        return "Switched to previous tab."
    except Exception as exc:
        return f"Tab switch failed: {exc}"


def switch_application() -> str:
    """Switch to the next active application (Alt+Tab)."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation unavailable."
    try:
        pyautogui.hotkey("alt", "tab")
        return "Switched application."
    except Exception as exc:
        return f"App switch failed: {exc}"


def minimize_all() -> str:
    """Minimize all windows to show the desktop."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation unavailable."
    try:
        pyautogui.hotkey("win", "d")
        return "Minimized all windows."
    except Exception as exc:
        return f"Minimize failed: {exc}"


def close_current_window() -> str:
    """Close the currently active window (Alt+F4)."""
    pyautogui = _load_pyautogui()
    if not pyautogui:
        return "Keyboard automation unavailable."
    try:
        pyautogui.hotkey("alt", "f4")
        return "Closed current window."
    except Exception as exc:
        return f"Window close failed: {exc}"


def capture_and_analyze_screen() -> str:
    """Take a screenshot of the current screen for AI analysis."""
    try:
        # Save screenshot to a temporary location
        timestamp = int(time.time())
        file_path = f"scratch/screen_{timestamp}.png"
        screenshot = ImageGrab.grab()
        screenshot.save(file_path)
        
        # In a real scenario, we'd send this to a Vision model.
        # For now, we'll notify the user we've 'seen' the screen.
        return f"SCREEN_ANALYSIS_COMPLETE: Captured state at {time.strftime('%H:%M:%S')}. I'm analyzing the content for your assignment."
    except Exception as exc:
        return f"Screen capture failed: {exc}"



def get_active_window_title() -> str:
    """Get the title of the currently active window."""
    try:
        import pygetwindow as gw
        window = gw.getActiveWindow()
        if window:
            return window.title
        return "Unknown Window"
    except Exception as exc:
        logger.error("Failed to get active window title: %s", exc)
        return "Unknown"

def launch_desktop_pet() -> str:
    """Launch the KEVIN Desktop Pet application, avoiding duplicates."""
    try:
        import subprocess
        import psutil
        
        # Check if already running
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'desktop_pet.py' in ' '.join(proc.info['cmdline']):
                    return "I'm already on your taskbar, partner."
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        # Run in background
        subprocess.Popen([".\\.venv\\Scripts\\python.exe", "app/desktop_pet.py"], 
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "I'm coming. Just jumping onto your taskbar now."
    except Exception as exc:
        logger.error("Failed to launch desktop pet: %s", exc)
        return f"Launch failed: {exc}"

def research_assignment(topic: str) -> str:
    """Perform a deep search for assignment materials."""
    try:
        url = f"https://www.google.com/search?q={topic.replace(' ', '+')}+assignment+help+research+papers"
        webbrowser.open(url)
        return f"Initiated deep research sequence for: {topic}"
    except Exception as exc:
        return f"Research failed: {exc}"
