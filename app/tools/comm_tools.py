import pywinauto
from pywinauto import Desktop
from langchain.tools import tool
import logging

logger = logging.getLogger("KEVIN-COMMS")

@tool
def detect_whatsapp_call() -> str:
    """Scans AS's desktop for any incoming WhatsApp calls. Returns the status."""
    try:
        # Looking for windows containing 'WhatsApp' with 'Call' in text
        windows = Desktop(backend="uia").windows()
        for w in windows:
            title = w.window_text()
            if "WhatsApp" in title and ("Incoming" in title or "Call" in title):
                return f"Kevin Alert: AS, you have an incoming WhatsApp call from '{title.split(' - ')[0]}'. Should I answer it?"
        
        return "No incoming calls detected right now, AS."
    except Exception as e:
        return f"Error scanning for calls: {e}"

@tool
def answer_whatsapp_call() -> str:
    """Automatically answers an active incoming WhatsApp call. Your proactive partner in action!"""
    try:
        windows = Desktop(backend="uia").windows()
        for w in windows:
            if "WhatsApp" in w.window_text() and ("Incoming" in w.window_text() or "Call" in w.window_text()):
                # Try to find the 'Accept' or 'Answer' button
                # WhatsApp Desktop typically uses 'Accept'
                accept_btn = w.child_window(title="Accept", control_type="Button")
                if accept_btn.exists():
                    accept_btn.click()
                    return "Kevin: Call accepted! I'm on it, AS."
                
                # Fallback for different versions
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
    # This is a broader scan for any high-priority windows
    try:
        windows = Desktop(backend="uia").windows()
        important = []
        for w in windows:
            t = w.window_text()
            if any(word in t for word in ["WhatsApp", "Telegram", "Discord", "Teams"]):
                if "1" in t or "new" in t.lower() or "incoming" in t.lower():
                    important.append(t)
        
        if important:
            return f"Kevin: AS, you have some important updates: {', '.join(important)}"
        return "Everything looks quiet, AS. Focus on your work!"
    except Exception as e:
        return f"Error checking notifications: {e}"
