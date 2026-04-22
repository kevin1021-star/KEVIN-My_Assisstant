import sys
import json
import asyncio
import threading
import websockets
import pyttsx3
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize
from PyQt6.QtGui import QPixmap, QMovie, QPainter, QColor

class DesktopPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KEVIN_PARTNER")
        
        # Initialize TTS
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        # Try to find a male/boy voice
        for voice in voices:
            if "male" in voice.name.lower() or "david" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 160) # Natural speed
        
        # Transparent, Frameless, Always on Top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Make him non-blocking so you can click through him to your work
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Speech Bubble (Hidden by default)
        self.bubble = QLabel("")
        self.bubble.setStyleSheet("""
            background: rgba(10, 10, 10, 220);
            border: 2px solid #ff0033;
            border-radius: 10px;
            color: white;
            padding: 10px;
            font-family: 'JetBrains Mono';
            font-size: 12px;
        """)
        self.bubble.setWordWrap(True)
        self.bubble.hide()
        self.layout.addWidget(self.bubble)

        # Status Badge (HEARING_YOU / THINKING)
        self.status_badge = QLabel("")
        self.status_badge.setStyleSheet("""
            background: #ff0033;
            color: white;
            padding: 2px 8px;
            font-size: 9px;
            font-family: 'JetBrains Mono';
            border-radius: 5px;
        """)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.hide()
        self.layout.addWidget(self.status_badge)

        # Character Figure
        self.label = QLabel()
        self.pixmap = QPixmap("app/static/img/kevin_anime.png")
        # Resize to a reasonable pet size
        self.pixmap = self.pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(self.pixmap)
        self.layout.addWidget(self.label)
        
        # Positioning (Bottom Right above taskbar)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - 320, screen.height() - 350)
        
        # State for dragging
        self.drag_pos = QPoint()
        
        # Connect to Backend
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        
        # Timers for animations
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate_idle)
        self.timer.start(100)
        self.anim_frame = 0

    def _run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_ws())

    async def _connect_ws(self):
        uri = "ws://localhost:8000/ws/chat"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    print("[PET] Connected to brain.")
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        if data.get("type") == "chat":
                            self._show_speech(data.get("content"))
                        elif data.get("type") == "status" and "listening" in data.get("message", "").lower():
                            self.status_badge.setText("HEARING_YOU...")
                            self.status_badge.show()
                        elif data.get("type") == "telemetry":
                            # Reset status if not hearing
                            if not getattr(self, 'is_talking', False):
                                self.status_badge.hide()
            except Exception as e:
                print(f"[PET] Connection lost: {e}")
                await asyncio.sleep(3)

    def send_to_brain(self, text):
        """Send user input from the pet to the AI brain."""
        if hasattr(self, 'websocket') and self.websocket.open:
            asyncio.run_coroutine_threadsafe(self.websocket.send(text), self.loop)

    def _show_speech(self, text):
        self.bubble.setText(text)
        self.bubble.show()
        
        # Humanoid Voice Output
        threading.Thread(target=self._speak, args=(text,), daemon=True).start()
        
        # Animated "Talking" state
        self.is_talking = True
        QTimer.singleShot(8000, self._stop_talking)

    def _speak(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            pass

    def _stop_talking(self):
        self.bubble.hide()
        self.is_talking = False

    def _animate_idle(self):
        self.anim_frame += 0.05
        import math
        
        # Subtle "Breathing" and "Swaying"
        bob = int(math.sin(self.anim_frame) * 8)
        sway = math.sin(self.anim_frame * 0.5) * 3
        
        # Apply transformation
        self.label.setContentsMargins(int(sway + 10), 0, 10, bob + 10)
        
        # Talking pulse
        if getattr(self, 'is_talking', False):
            glow = int(128 + math.sin(self.anim_frame * 10) * 127)
            self.label.setStyleSheet(f"border-radius: 150px; background-color: rgba(255, 0, 51, {glow/1000});")
        else:
            self.label.setStyleSheet("")

        self._check_mouse_proximity()

    def _check_mouse_proximity(self):
        """If the mouse gets too close, KEVIN steps aside immediately."""
        from PyQt6.QtGui import QCursor
        cursor_pos = QCursor.pos()
        pet_rect = self.geometry()
        
        # Inflate the detection area
        detection_rect = pet_rect.adjusted(-100, -100, 100, 100)
        
        if detection_rect.contains(cursor_pos):
            screen = QApplication.primaryScreen().availableGeometry()
            # If mouse is on the right, move left, and vice versa
            target_x = 50 if cursor_pos.x() > screen.width() // 2 else screen.width() - 350
            target_y = pet_rect.y() # Keep current height
            
            # Snap to a corner if he's still in the way
            if abs(cursor_pos.y() - target_y) < 200:
                target_y = 50 if cursor_pos.y() > screen.height() // 2 else screen.height() - 400
                
            self._slide_to(target_x, target_y)

    def _slide_to(self, x, y):
        """Smoothly move to the target position."""
        # Simple linear interpolation for sliding effect
        curr_x, curr_y = self.x(), self.y()
        step_x = (x - curr_x) / 5
        step_y = (y - curr_y) / 5
        self.move(int(curr_x + step_x), int(curr_y + step_y))

    def mouseDoubleClickEvent(self, event):
        """Toggle size between small and large on double click."""
        current_width = self.label.pixmap().width()
        new_size = 450 if current_width < 400 else 250
        self.pixmap = QPixmap("app/static/img/kevin_anime.png").scaled(
            new_size, new_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.label.setPixmap(self.pixmap)
        self.resize(new_size, new_size + 100)

    # Allow dragging KEVIN around
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec())
