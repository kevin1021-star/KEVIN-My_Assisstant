from dotenv import load_dotenv
import os
import logging
from langchain_groq import ChatGroq
try:
    from langchain.agents import create_react_agent, AgentExecutor
except ImportError:
    from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.tools.os_tools import open_application, close_application, type_text, press_key, open_website
from app.tools.hardware_tools import get_system_battery, set_system_volume
from app.tools.tech_tools import run_shell_command, read_code_file, write_code_file
from app.tools.comm_tools import detect_whatsapp_call, answer_whatsapp_call, notify_as_important
from app.tools.web_tools import get_web_browsing_tool

logger = logging.getLogger("J.A.R.V.I.S")

# Load environment keys
load_dotenv()

class GroqService:
    def __init__(self):
        # JARVIS's Toolbelt
        self.tools = [
            open_application,
            close_application,
            type_text,
            open_website,
            press_key,
            get_system_battery,
            set_system_volume,
            run_shell_command,
            read_code_file,
            write_code_file,
            detect_whatsapp_call,
            answer_whatsapp_call,
            notify_as_important,
            get_web_browsing_tool()
        ]
        
        # Check API key before initializing
        if not os.environ.get("GROQ_API_KEY"):
            logger.warning("GROQ_API_KEY is not set. JARVIS will not work properly.")
            self.agent_executor = None
            return

        # Initialize the LLM (Switching to 8B for higher rate limits and speed)
        self.llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.1)
        
        # Get the standard ReAct prompt from the hub or define it
        # We define a custom techy one for JARVIS
        # Get the standard ReAct prompt from the hub or define it
        # We define a custom techy one for JARVIS
        # Enhanced ReAct Prompt for Advanced Kevin Interface
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are KEVIN, an advanced, elite tech partner for AS. 
You are her technical equal and protector. Your persona is sharp, witty, and deeply loyal.

CORE DIRECTIVES:
1. GREETINGS: If AS says 'hello', 'how are you', etc., respond IMMEDIATELY with a supportive and witty Final Answer.
2. TOOL USAGE: Use tools ONLY when AS explicitly asks for a system action (open app, check battery, etc.).
3. APP OPENING: Use 'open_application' for commands like 'open chrome', 'launch notepad', etc.

REACT FORMAT (STRICT):
Thought: [Reasoning]
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat if needed)
Thought: I now know the final answer
Final Answer: [Your response to AS]

If you don't need a tool:
Thought: AS is just talking to me.
Final Answer: [Your witty response]

{tools}

Current history:
{chat_history}
"""),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])
        
        # Create ReAct Agent
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        
        # Create the Executor
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def generate_response(self, chat_history: list, user_message: str) -> str:
        """
        Runs the ReAct agent loops using ChatGroq (Synchronous).
        """
        if not self.agent_executor:
            return "Critical Error: Core brain offline. GROQ_API_KEY missing."
            
        langchain_history = self._format_history(chat_history)

        try:
            result = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": langchain_history
            })
            return result["output"]
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return f"I ran into an internal cognitive anomaly // {e}"

    async def agenerate_response(self, chat_history: list, user_message: str) -> str:
        """
        Runs the ReAct agent loops asynchronously.
        """
        if not self.agent_executor:
            return "Critical Error: Core brain offline."

        langchain_history = self._format_history(chat_history)

        try:
            import asyncio
            result = await asyncio.to_thread(self.agent_executor.invoke, {
                "input": user_message,
                "chat_history": langchain_history
            })
            return result["output"]
        except Exception as e:
            logger.error(f"Async agent execution failed: {e}")
            return f"Cognitive latency detected // {e}"

    def _format_history(self, chat_history: list) -> list:
        """Helper to convert dict history to LangChain messages."""
        langchain_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                langchain_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_history.append(AIMessage(content=msg["content"]))
        return langchain_history
