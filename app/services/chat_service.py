import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict
import uuid

from config import CHATS_DATA_DIR, MAX_CHAT_HISTORY_TURNS
from app.model import ChatMessage, ChatHistory
from app.services.groq_service import GroqService
from app.services.memory_service import log_conversation


logger = logging.getLogger("J.A.R.V.I.S")


class ChatService:
    """
    Manage chat sessions: in-memory message lists, load/save to disk, and 
    calling Groq to get replies. All state for active sessions is in 
    self.sessions; saving to disk is done after each message so 
    conversations survive restarts.
    """
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service 
        # Map: session_id -> list of chatmessages (user and assistant messages in order).
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def get_or_create_session(self, session_id: str) -> List[ChatMessage]:
        """Returns the message history for a session_id, loading from disk if necessary."""
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try to load from disk
        file_path = CHATS_DATA_DIR / f"{session_id}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages = [ChatMessage(**msg) for msg in data.get("messages", [])]
                    self.sessions[session_id] = messages
                    logger.info(f"Loaded session {session_id} from disk.")
                    return messages
            except Exception as e:
                logger.error(f"Failed to load session {session_id}: {e}")

        # If it doesn't exist, create a new one
        self.sessions[session_id] = []
        return self.sessions[session_id]

    def save_session(self, session_id: str):
        """Saves session messages to disk as JSON."""
        if session_id not in self.sessions:
            return

        file_path = CHATS_DATA_DIR / f"{session_id}.json"
        try:
            # We wrap the messages in a ChatHistory model for better validation
            history = ChatHistory(session_id=session_id, messages=self.sessions[session_id])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(history.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")

    async def process_message(self, session_id: str, user_text: str) -> str:
        """Adds user message, calls Groq (async), saves, and returns assistant reply."""
        history = self.get_or_create_session(session_id)
        
        # Add user message
        history.append(ChatMessage(role="user", content=user_text))
        log_conversation("user", user_text)
        
        # Trim history for LLM context window
        context_history = self._get_context_window(history)
        
        # Generate response (using async version)
        response_text = await self.groq_service.agenerate_response(context_history, user_text)
        
        # Add assistant message
        history.append(ChatMessage(role="assistant", content=response_text))
        log_conversation("assistant", response_text)
        
        # Save to disk
        self.save_session(session_id)
        
        return response_text

    def _get_context_window(self, history: List[ChatMessage]) -> List[dict]:
        """Formats the last N turns for the LLM."""
        # Each turn is 2 messages (user, assistant)
        limit = MAX_CHAT_HISTORY_TURNS * 2
        recent = history[-limit:]
        return [{"role": m.role, "content": m.content} for m in recent]