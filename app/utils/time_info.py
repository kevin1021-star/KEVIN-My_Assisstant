from datetime import datetime

def get_time_greeting() -> str:
    """Returns a time-appropriate greeting for Kevin to use."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Hey there"

def get_current_time_str() -> str:
    """Returns the current time in a readable format."""
    return datetime.now().strftime("%I:%M %p")
