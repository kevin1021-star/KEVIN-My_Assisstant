import psutil
import os

def get_system_battery() -> str:
    """Returns the current battery percentage and whether it is plugged in."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "Battery information is not available on this system."
        
        status = "plugged in" if battery.power_plugged else "unplugged"
        return f"Battery is at {battery.percent}% and is currently {status}."
    except Exception as e:
        return f"Error fetching battery status: {e}"

def set_system_volume(level: int) -> str:
    """Sets the master system volume. Level should be between 0 and 100."""
    try:
        # volume control depends on OS, this is for Windows using nircmd or similar
        # But we can use pyautogui for a simple relative control if nircmd isn't there
        # For a truly 'advanced' feel, we'll use 'sound_control' script or PowerShell
        # Using PowerShell for Windows volume control
        level = max(0, min(100, int(level)))
        # This PS command sets the volume. Note: standard PS doesn't have a direct 'set volume'
        # so we often use a small helper or specialized COM objects.
        # Simplified for now using a common trick:
        os.system(f"powershell -Command \"(new-object -com wscript.shell).SendKeys([char]174)*50; (new-object -com wscript.shell).SendKeys([char]175)*{level//2}\"")
        return f"System volume adjusted to approximately {level}%."
    except Exception as e:
        return f"Error setting volume: {e}"
