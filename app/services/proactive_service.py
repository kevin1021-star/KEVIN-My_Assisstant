import asyncio
import time
import logging
import psutil
from app.services.memory_service import get_state
from app.tools.os_tools import get_active_window_title

logger = logging.getLogger("KEVIN-PROACTIVE")

# List of allowed work apps in strict mode
WORK_APPS = ["code", "obsidian", "command prompt", "powershell", "terminal", "cursor", "localhost"]

# List of slacking apps to aggressively close in strict mode
SLACK_APPS = ["netflix", "youtube", "prime video", "disney", "movies", "games", "steam", "epic games"]

class ProactiveService:
    def __init__(self):
        self.is_running = False
        self.websocket_manager = None
        
    def start(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.is_running = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("Proactive monitoring started.")

    async def _monitoring_loop(self):
        while self.is_running:
            try:
                strict_mode = get_state("strict_mode", "false") == "true"
                current_task = get_state("current_task", "")
                
                window_title = get_active_window_title().lower()
                
                if strict_mode and window_title and window_title != "unknown":
                    # Check if they are slacking
                    is_slacking = any(app in window_title for app in SLACK_APPS)
                    is_working = any(app in window_title for app in WORK_APPS)
                    
                    if is_slacking or (not is_working and len(window_title) > 0 and window_title != "unknown window" and "jarvis" not in window_title and "kevin" not in window_title):
                        # Force close the distraction
                        self._force_close_active_window()
                        
                        # Scold the user
                        scold_msg = f"Oi! Mujhe bewakoof mat bana. Tune bola tha tujhe '{current_task}' aaj hi complete karna hai. Ye bakwas band kar aur kaam pe lag warna system lock kar dunga!"
                        if self.websocket_manager:
                            await self.websocket_manager.broadcast_message({
                                "type": "alert",
                                "message": scold_msg
                            })
                            
                        # Give them 10 seconds to recover before checking again
                        await asyncio.sleep(10)
                        
            except Exception as e:
                logger.error(f"Proactive loop error: {e}")
                
            await asyncio.sleep(3) # Check every 3 seconds
            
    def _force_close_active_window(self):
        import pygetwindow as gw
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                active_window.close()
        except Exception as e:
            logger.error(f"Failed to close window: {e}")
            
proactive_tracker = ProactiveService()
