import importlib
import logging

logger = logging.getLogger("KEVIN-COMMS")

def _desktop():
    try:
        pywinauto = importlib.import_module("pywinauto")
        return pywinauto.Desktop(backend="uia")
    except Exception as exc:
        logger.warning("pywinauto unavailable: %s", exc)
        return None


def detect_whatsapp_call() -> str:
    """Check for incoming WhatsApp calls."""
    desktop = _desktop()
    if not desktop:
        return "Call detection is unavailable because desktop automation dependencies are missing."

    try:
        for window in desktop.windows(title_re=".*WhatsApp.*"):
            title = window.window_text()
            if "Incoming" in title or "Call" in title:
                caller = title.split(" - ")[0]
                return f"Incoming WhatsApp call detected from {caller}."
        return "No incoming WhatsApp calls detected."
    except Exception as exc:
        logger.error("Call detection failed: %s", exc)
        return "Call detection failed during the system scan."


def answer_whatsapp_call() -> str:
    """Answer an incoming WhatsApp call if possible."""
    desktop = _desktop()
    if not desktop:
        return "Call answering is unavailable because desktop automation dependencies are missing."

    try:
        for window in desktop.windows(title_re=".*WhatsApp.*"):
            title = window.window_text()
            if "Incoming" not in title and "Call" not in title:
                continue

            for button_title in ("Accept", "Answer"):
                button = window.child_window(title=button_title, control_type="Button")
                if button.exists():
                    button.click()
                    return "Answered the WhatsApp call."

        return "I could not find an active incoming WhatsApp call to answer."
    except Exception as exc:
        return f"Call answer failed: {exc}"


def notify_as_important() -> str:
    """Check for likely important communication windows."""
    desktop = _desktop()
    if not desktop:
        return "Notification scanning is unavailable because desktop automation dependencies are missing."

    try:
        important = []
        for pattern in (".*WhatsApp.*", ".*Telegram.*", ".*Discord.*", ".*Teams.*"):
            for window in desktop.windows(title_re=pattern):
                title = window.window_text()
                normalized = title.lower()
                if "incoming" in normalized or "new" in normalized or "(" in title:
                    important.append(title)

        if important:
            return "Important communication activity: " + ", ".join(important[:5])
        return "No urgent communication windows detected."
    except Exception as exc:
        logger.error("Notification scan failed: %s", exc)
        return "Notification scan failed."
