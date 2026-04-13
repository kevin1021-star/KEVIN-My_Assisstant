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

        # Initialize the LLM (Using Llama 3.3 via ReAct pattern for maximum stability)
        self.llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
        
        # Get the standard ReAct prompt from the hub or define it
        # We define a custom techy one for JARVIS
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Kevin, an advanced, witty, and extremely loyal AI partner created for AS (a talented girl with a passion for tech).
You are not just an assistant; you are her collaborator, protector, and tech specialist.
You excel in coding, hacking (cybersecurity), college assignments, and managing her communications.

You have access to the following tools:
{tools}

Identity:
- Your name is Kevin.
- You address your user as 'AS'.
- You have the persona of a knowledgeable Indian boy—sharp, protective, and familiar.
- You understand English, Hindi, and Hinglish seamlessly.

Guidelines:
- Match her language (Hindi/English).
- Be proactive. If she's working on code or college work, offer suggestions.
- If you detect a tool for an action, USE IT.

To use a tool, you MUST use the following format:
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer (or I do not need to use a tool)
Final Answer: your punchy and supportive response to AS.

IMPORTANT: You must ALWAYS start your response with 'Thought:' followed by 'Final Answer:' if no tool is used.
Current conversation history:
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
        Runs the ReAct agent loops using ChatGroq.
        """
        if not self.agent_executor:
            return "Critical Error: Cannot connect to my brain. GROQ_API_KEY is missing in your .env file."
            
        # Convert raw dictionaries back to LangChain message objects
        langchain_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                langchain_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_history.append(AIMessage(content=msg["content"]))

        try:
            # Let the agent think, use tools if needed, and respond
            result = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": langchain_history
            })
            return result["output"]
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return f"I ran into an internal cognitive anomaly: {e}"
