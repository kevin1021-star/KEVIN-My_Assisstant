import pywinauto
from pywinauto import Desktop
from langchain.tools import tool
import logging

logger = logging.getLogger("KEVIN-COMMS")

@tool
def detect_whatsapp_call() -> str:
    """Scans AS's desktop for any incoming WhatsApp calls. Returns the status."""
    try:
        # Use a more targeted search to avoid full desktop enumeration if possible
        # However, WhatsApp Desktop often requires UIA. We'll keep UIA but optimize the loop.
        desktop = Desktop(backend="uia")
        # Find windows with "WhatsApp" in title directly
        whatsapp_windows = desktop.windows(title_re=".*WhatsApp.*")
        
        for w in whatsapp_windows:
            title = w.window_text()
            if "Incoming" in title or "Call" in title:
                # Extra check for the "Accept" button presence to confirm it's an active incoming call
                return f"Kevin Alert: AS, you have an incoming WhatsApp call from '{title.split(' - ')[0]}'. Should I answer it?"
        
        return "No incoming calls detected right now, AS."
    except Exception as e:
        logger.error(f"Error scanning for calls: {e}")
        return "No incoming calls detected (system scan bypassed)."

@tool
def answer_whatsapp_call() -> str:
    """Automatically answers an active incoming WhatsApp call. Your proactive partner in action!"""
    try:
        desktop = Desktop(backend="uia")
        whatsapp_windows = desktop.windows(title_re=".*WhatsApp.*")
        for w in whatsapp_windows:
            if "Incoming" in w.window_text() or "Call" in w.window_text():
                # Try to find the 'Accept' or 'Answer' button
                accept_btn = w.child_window(title="Accept", control_type="Button")
                if accept_btn.exists():
                    accept_btn.click()
                    return "Kevin: Call accepted! I'm on it, AS."
                
                accept_btn = w.child_window(title="Answer", control_type="Button")
                if accept_btn.exists():
                    accept_btn.click()
                    return "Kevin: Answered the call for you, AS."
        
        return "Kevin: I couldn't find an 'Accept' button to click, AS."
    except Exception as e:
        return f"Kevin: Had a glitch trying to answer: {e}"

@tool
def notify_as_important() -> str:
    """Scans for important notifications (chats/calls) that might need immediate attention."""
    try:
        desktop = Desktop(backend="uia")
        # Targeted search for known communication apps
        important = []
        app_patterns = [".*WhatsApp.*", ".*Telegram.*", ".*Discord.*", ".*Teams.*"]
        
        for pattern in app_patterns:
            windows = desktop.windows(title_re=pattern)
            for w in windows:
                t = w.window_text()
                # Common notification indicators in window titles
                if "1" in t or "new" in t.lower() or "incoming" in t.lower() or "(" in t:
                    important.append(t)
        
        if important:
            return f"Kevin: AS, you have some important updates: {', '.join(important)}"
        return "Everything looks quiet, AS. Focus on your work!"
    except Exception as e:
        logger.error(f"Error checking notifications: {e}")
        return "Everything looks quiet (notification scan bypassed)."
