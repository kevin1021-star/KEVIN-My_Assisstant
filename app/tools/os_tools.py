import sys
import os
from langchain.tools import tool
import pyautogui
from AppOpener import open as app_open, close as app_close
import webbrowser

@tool
def open_application(app_name: str) -> str:
    """Opens an application on the Windows computer by its name. Example: open_application('spotify')"""
    try:
        app_open(app_name, match_closest=True)
        return f"Successfully opened {app_name}."
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"

@tool
def close_application(app_name: str) -> str:
    """Closes an open application on the Windows computer by its name. Example: close_application('notepad')"""
    try:
        app_close(app_name, match_closest=True)
        return f"Successfully closed {app_name}."
    except Exception as e:
        return f"Error closing {app_name}: {str(e)}"

@tool
def type_text(text: str) -> str:
    """Types text dynamically onto the current active window using the keyboard. Useful for writing emails, filling forms, or coding!"""
    try:
        pyautogui.write(text, interval=0.01)
        return f"Successfully typed: {text}"
    except Exception as e:
        return f"Failed to type: {e}"

@tool
def press_key(key: str) -> str:
    """Presses a specific keyboard key (e.g. 'enter', 'tab', 'win', 'space')."""
    try:
        pyautogui.press(key)
        return f"Successfully pressed the '{key}' key."
    except Exception as e:
        return f"Failed to press key: {e}"

@tool
def open_website(url: str) -> str:
    """Opens a website URL in the default web browser. Example: open_website('https://www.google.com')"""
    try:
        webbrowser.open(url)
        return f"Successfully opened website: {url}"
    except Exception as e:
        return f"Error opening website {url}: {str(e)}"
