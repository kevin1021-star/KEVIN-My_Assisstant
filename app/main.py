import os
import json
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

from app.services.gesture_service import GestureService

# Initialize Services
groq_service = GroqService()
chat_service = ChatService(groq_service)
gesture_service = GestureService()

gesture_queue = asyncio.Queue(maxsize=32)

async def gesture_processor_task():
    """Consumes gestures from the queue as fast as possible without blocking main chat."""
    while True:
        data = await gesture_queue.get()
        try:
            if data.get("mode") == "MOUSE":
                gesture_service.process_mouse_sync(
                    data.get("x"),
                    data.get("y"),
                    data.get("click", False),
                    data.get("right_click", False),
                    data.get("drag", False),
                    data.get("scroll_delta", 0.0),
                )
        except Exception as e:
            logger.error(f"Gesture processing error: {e}")
        finally:
            gesture_queue.task_done()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(gesture_processor_task())

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serves the advanced JARVIS techy HUD."""
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except TypeError:
        return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "groq_configured": bool(os.environ.get("GROQ_API_KEY")),
        "telemetry": True,
    }


async def system_telemetry_pusher(websocket: WebSocket):
    """Background task to push metrics and proactively detect calls (optimized)."""
    try:
        last_call_check = 0
        while True:
            # Telemetry every 2 seconds
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            await websocket.send_json({
                "type": "telemetry",
                "cpu": cpu,
                "ram": ram,
            })

            # Proactive Call Detection every 10 seconds to reduce CPU burden
            current_time = asyncio.get_event_loop().time()
            if current_time - last_call_check > 10:
                call_status = await asyncio.to_thread(detect_whatsapp_call)
                if "Incoming" in call_status:
                    await websocket.send_json({
                        "type": "alert",
                        "message": call_status
                    })
                last_call_check = current_time

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
            # Handle both text and JSON messages
            try:
                message = await websocket.receive()
            except RuntimeError:
                break
            
            if "text" in message:
                user_input = message["text"]
                
                # Check if it's JSON
                try:
                    data = json.loads(user_input)
                    if data.get("type") == "gesture":
                        # Put in non-blocking queue
                        try:
                            # Map to old internal format for processor_task
                            processed_data = {
                                "mode": "MOUSE",
                                "x": data.get("x"),
                                "y": data.get("y"),
                                "click": data.get("action") == "click",
                                "right_click": data.get("action") == "right_click"
                            }
                            gesture_queue.put_nowait(processed_data)
                        except asyncio.QueueFull:
                            pass 
                        continue
                except json.JSONDecodeError:
                    user_text = user_input
                
                user_text = user_text.strip()
                if not user_text:
                    continue

                logger.info(f"Received directive: {user_text}")
                response_text = await chat_service.process_message(session_id, user_text)
                await websocket.send_json({
                    "type": "chat",
                    "content": response_text
                })
            
    except WebSocketDisconnect:
        logger.info("Client disconnected from HUD.")
        gesture_service.reset()
    finally:
        telemetry_task.cancel()
        gesture_service.reset()
