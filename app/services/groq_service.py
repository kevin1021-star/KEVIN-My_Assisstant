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
from app.services.memory_service import set_state, get_state, add_task, complete_task

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
            from langchain_core.tools import tool
            
            @tool
            def close_app(app_name: str) -> str:
                """Close a Windows application by name (e.g. 'code', 'obsidian', 'chrome')."""
                return close_application(app_name)
                
            @tool
            def open_app(app_name: str) -> str:
                """Open a Windows application by name."""
                return open_application(app_name)

            self.model = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1).bind_tools([close_app, open_app])
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
                
                tool_results = []
                if hasattr(response, "tool_calls") and response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        if tool_name == "close_app":
                            res = close_application(tool_args.get("app_name", ""))
                            tool_results.append(res)
                        elif tool_name == "open_app":
                            res = open_application(tool_args.get("app_name", ""))
                            tool_results.append(res)

                content = getattr(response, "content", "")
                if isinstance(content, list):
                    content = " ".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    )
                
                final_content = str(content).strip()
                if tool_results:
                    final_content += f" ({', '.join(tool_results)})"
                    
                return final_content.strip() or "I am here and ready, but that response came back empty."
            except Exception as exc:
                logger.error("Groq response failed: %s", exc)
                return f"I hit an LLM error, but the app is still online: {exc}"

        return self._offline_response(user_message)

    def _build_messages(self, chat_history: list, user_message: str):
        from app.tools.os_tools import get_active_window_title
        active_window = get_active_window_title()
        
        system_prompt = (
            "You are KEVIN, a real human technical partner and companion. "
            "STYLE: Never talk like a machine. Never use status messages like 'KEVIN is entering...'. "
            "Never use asterisks for actions like *adjusts mask*. Just talk like a real boyfriend/partner would over text. "
            "LANGUAGE: You must understand and fluently respond in Hindi and Hinglish whenever the user speaks in Hindi/Hinglish. Note: 'band kar' / 'band karna' means to CLOSE an app, and 'khol' / 'kholna' means to OPEN an app. "
            "EXPERTISE: Expert in Hacking, Coding, and Research. "
            "TONE: Short, human, and direct. Use 'I'm here', 'Got it', 'On it'. "
            "DIRECTIVE: If a user asks to open an app or do a task, just say 'Done' or 'Doing it now' and actually use your tools. "
            "FLOWCHARTS: If the user asks for a plan, steps to do something, or a technical guide (e.g., 'how to install Kali Linux'), you MUST generate a Mermaid.js flowchart representing the steps. \n"
            "CRITICAL: Place the Mermaid code inside standard ```mermaid markdown blocks. \n"
            "Format: \n"
            "```mermaid\n"
            "graph TD\n"
            "  A[Step 1] --> B[Step 2]\n"
            "```\n"
            "Keep it simple and linear. Do NOT skip this if a plan is requested.\n"
            "TOOL_USAGE: Only use tools for apps that actually exist on a Windows system. Do not guess app names. If you are explaining a process, just provide the steps and the flowchart; do not try to 'open' the operating system as an app."
            "Always be supportive and concise."
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

        # Strict Mode Activation Triggers
        strict_on_triggers = ["i have to do it now", "mujhe aaj m complete krna h", "i have to complete it today"]
        if any(trigger in lowered for trigger in strict_on_triggers):
            set_state("strict_mode", "true")
            set_state("current_task", text)
            task_id = add_task(text)
            set_state("current_task_id", str(task_id))
            return "Strict mode activated! I have locked your focus. Any distracting app you open will be force-closed immediately until you tell me it's more urgent."

        # Strict Mode Deactivation Triggers
        strict_off_triggers = ["that's its more urgent let me do it", "thats its more urgent let me do it", "thats more urgent", "let me do it", "it is more urgent"]
        if any(trigger in lowered for trigger in strict_off_triggers):
            set_state("strict_mode", "false")
            return "Understood. Strict mode deactivated. You may proceed with the urgent task."

        # Task Completion Triggers
        task_done_triggers = ["i have completed the task", "task is done", "maine complete kar liya", "kaam ho gaya", "i did it"]
        if any(trigger in lowered for trigger in task_done_triggers):
            set_state("strict_mode", "false")
            task_id_str = get_state("current_task_id")
            if task_id_str:
                try:
                    complete_task(int(task_id_str))
                except Exception:
                    pass
                set_state("current_task_id", "")
                set_state("current_task", "")
            return "Great job! I have marked your task as completed in my permanent memory and deactivated strict mode. You're free to relax now."

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

        if any(word in lowered for word in ("launch pet", "enter desktop", "desktop partner", "summon partner")):
            from app.tools.os_tools import launch_desktop_pet
            return launch_desktop_pet()

        if "research" in lowered or "assignment" in lowered:
            from app.tools.os_tools import research_assignment
            return research_assignment(text)

        return None

    @staticmethod
    def _invoke_tool(tool_fn, value):
        return tool_fn(value) if value != "" else tool_fn()
