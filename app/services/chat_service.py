"""
CHAT SERVICE MODULE
===================



import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
import uuid

from config import CHATS_DATA_DIR, MAX_CHAT_HISTORY_TURNS
from app.models import ChatMessage, ChatHistory
from app.services.groq_service import GroqService
from app.service.realtime_service import RealtimeGroqService

logger = logging.getLogger("K.E.V.I.N")

class chatservice:
   ersations survive restarts.
    """
    def __init__(self, groq_service, realtime_service: RealtimeGroqService = None):
        """store reference to the groq and realtime services; keep sessions in memory."""
        self.groq_service = groq_service 
        self.realtime_service = realtime_service
        
        self.sessions: Dict[str, List[chatMessage]] = {}

        
        
