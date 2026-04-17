import logging
import os
import re
from urllib.parse import quote_plus

from dotenv import load_dotenv

from app.tools.comm_tools import answer_whatsapp_call, detect_whatsapp_call, notify_as_important
from app.tools.hardware_tools import get_system_battery, set_system_volume
from app.tools.os_tools import (
    close_application, open_application, open_website, press_key, type_text,
    switch_tab, previous_tab, switch_application, minimize_all, close_current_window
)
from app.tools.tech_tools import read_code_file, run_shell_command, write_code_file

logger = logging.getLogger("J.A.R.V.I.S")

load_dotenv()

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_groq import ChatGroq
except Exception:
    AIMessage = HumanMessage = SystemMessage = None
    ChatGroq = None


class GroqService:
    def __init__(self):
        self.model = None
        self.offline_notice = None
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            self.offline_notice = "Groq is not configured, so I can still help with built-in system actions and offline guidance."
            return

        if ChatGroq is None:
            self.offline_notice = "Groq support is installed incorrectly, so I am running in offline fallback mode."
            return

        try:
            self.model = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.2)
        except Exception as exc:
            logger.error("Failed to initialize Groq model: %s", exc)
            self.offline_notice = f"Groq initialization failed: {exc}"

    async def agenerate_response(self, chat_history: list, user_message: str) -> str:
        tool_result = self._run_direct_action(user_message)
        if tool_result:
            return tool_result

        if self.model and SystemMessage:
            try:
                import asyncio

                messages = self._build_messages(chat_history, user_message)
                response = await asyncio.to_thread(self.model.invoke, messages)
                content = getattr(response, "content", "")
                if isinstance(content, list):
                    content = " ".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    )
                return str(content).strip() or "I am here and ready, but that response came back empty."
            except Exception as exc:
                logger.error("Groq response failed: %s", exc)
                return f"I hit an LLM error, but the app is still online: {exc}"

        return self._offline_response(user_message)

    def _build_messages(self, chat_history: list, user_message: str):
        system_prompt = (
            "You are KEVIN (Kinetic Electronic Virtual Intelligent Network), a high-performance 'Iron Man' style workstation assistant. "
            "Your primary directive is to assist with Coding, Hacking, and University Assignments. "
            "TONE: Professional, efficient, and tech-noir. Use terms like 'Directive received', 'Analysis complete'. "
            "If the user mentions a quiz or needs to see the screen, suggest the 'SCAN_SCREEN' command. "
            "Always provide the highest quality technical support."
        )
        messages = [SystemMessage(content=system_prompt)]

        for message in chat_history[-12:]:
            role = message.get("role")
            content = message.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=user_message))
        return messages

    def _offline_response(self, user_message: str) -> str:
        prompt = user_message.strip()
        if self.offline_notice:
            return f"{self.offline_notice} You said: '{prompt}'. Ask me to open apps, check battery, set volume, run a safe command, or help with local tasks."
        return "The assistant is running in offline mode. I can still handle local actions and basic guidance."

    def _run_direct_action(self, user_message: str):
        text = user_message.strip()
        lowered = text.lower()

        if not text:
            return "I did not catch that. Try a short message or use the quick actions."

        if lowered in {"hi", "hello", "hey", "yo"}:
            return "KEVIN online. Tell me what you want to launch, inspect, or fix."

        if "battery" in lowered:
            return self._invoke_tool(get_system_battery, "")

        volume_match = re.search(r"(?:set|change).*(?:volume).*(\d{1,3})", lowered)
        if volume_match:
            return self._invoke_tool(set_system_volume, volume_match.group(1))

        if lowered.startswith("open website ") or lowered.startswith("visit "):
            return open_website(text.split(" ", 2)[-1].strip())

        if lowered.startswith("search ") or lowered.startswith("google "):
            query = text.split(" ", 1)[1].strip()
            return open_website(f"https://www.google.com/search?q={quote_plus(query)}")

        if lowered.startswith("open "):
            target = text[5:].strip().lower()
            # Clean up natural language fillers
            target = target.replace("my ", "").replace("the ", "").strip()
            
            if target.startswith("http://") or target.startswith("https://") or "." in target:
                url = target if target.startswith("http") else f"https://{target}"
                return open_website(url)
            
            # Direct mapping for common apps
            if "whatsapp" in target: target = "WhatsApp"
            if "chrome" in target: target = "chrome"
            if "code" in target or "vs code" in target: target = "Code"
            
            return open_application(target)

        if lowered.startswith("close "):
            return close_application(text[6:].strip())

        if lowered.startswith("type "):
            return type_text(text[5:].strip())

        if lowered.startswith("press "):
            return press_key(text[6:].strip())

        if lowered.startswith("run command "):
            return self._invoke_tool(run_shell_command, text[12:].strip())

        if lowered.startswith("read file "):
            return self._invoke_tool(read_code_file, text[10:].strip())

        if lowered.startswith("write file "):
            parts = text[11:].split("::", 1)
            if len(parts) != 2:
                return "Use: write file <path> :: <content>"
            return write_code_file(parts[0].strip(), parts[1].strip())

        if "whatsapp call" in lowered and any(word in lowered for word in ("detect", "check", "incoming")):
            return detect_whatsapp_call()

        if "answer whatsapp" in lowered or "pick the call" in lowered:
            return answer_whatsapp_call()

        if "important notifications" in lowered or "important updates" in lowered:
            return notify_as_important()

        # Desktop Navigation Commands
        if any(word in lowered for word in ("switch tab", "next tab")):
            return switch_tab()
        
        if any(word in lowered for word in ("previous tab", "last tab")):
            return previous_tab()

        if any(word in lowered for word in ("switch app", "next app", "change window")):
            return switch_application()

        if any(word in lowered for word in ("minimize all", "minimize everything", "show desktop")):
            return minimize_all()

        if any(word in lowered for word in ("close window", "exit app")):
            return close_current_window()

        if any(word in lowered for word in ("scan screen", "capture screen", "analyze screen")):
            from app.tools.os_tools import capture_and_analyze_screen
            return capture_and_analyze_screen()

        if "research" in lowered or "assignment" in lowered:
            from app.tools.os_tools import research_assignment
            return research_assignment(text)

        return None

    @staticmethod
    def _invoke_tool(tool_fn, value):
        return tool_fn(value) if value != "" else tool_fn()
