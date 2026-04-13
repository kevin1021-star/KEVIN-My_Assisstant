import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
import asyncio
import psutil

from app.services.chat_service import ChatService
from app.services.groq_service import GroqService
from app.tools.comm_tools import detect_whatsapp_call

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS-API")

app = FastAPI(title="JARVIS Backend")

# We will create these directories and mount them
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize Services
groq_service = GroqService()
chat_service = ChatService(groq_service)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serves the advanced JARVIS techy HUD."""
    try:
        # Modern FastAPI/Starlette signature
        return templates.TemplateResponse(request=request, name="index.html")
    except TypeError:
        # Older FastAPI/Starlette signature
        return templates.TemplateResponse("index.html", {"request": request})


async def system_telemetry_pusher(websocket: WebSocket):
    """Background task to push system metrics to the frontend."""
    try:
        while True:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else 100
            
            await websocket.send_json({
                "type": "telemetry",
                "cpu": cpu,
                "ram": ram,
                "battery": battery_percent
            })

            # Proactive Call Detection for Kevin
            call_status = detect_whatsapp_call.run("")
            if "Incoming" in call_status:
                await websocket.send_json({
                    "type": "alert",
                    "message": call_status
                })

            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Telemetry pusher error: {e}")

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = "JARVIS_MAIN_OVERRIDE" 
    
    # Run the telemetry pusher in the background for this websocket
    telemetry_task = asyncio.create_task(system_telemetry_pusher(websocket))
    
    try:
        while True:
            user_text = await websocket.receive_text()
            logger.info(f"Received from user: {user_text}")
            
            await websocket.send_json({"type": "status", "message": "processing"})
            response_text = chat_service.process_message(session_id, user_text)
            await websocket.send_json({"type": "response", "message": response_text})
            
    except WebSocketDisconnect:
        logger.info("Client disconnected from HUD.")
    finally:
        telemetry_task.cancel()
