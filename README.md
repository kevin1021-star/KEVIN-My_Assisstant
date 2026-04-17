# 🧊 KEVIN // Advanced Partner Interface (v5.0)

[![Hacker HUD](https://img.shields.io/badge/UI-HUD_V5.0-00f3ff?style=for-the-badge&logoColor=white)](file:///app/templates/index.html)
[![Neural Mouse](https://img.shields.io/badge/Vision-Neural_Mouse-ff003c?style=for-the-badge)](file:///app/static/js/main.js)
[![OCR](https://img.shields.io/badge/Intelligence-OCR_Script-8a2be2?style=for-the-badge)](file:///app/services/groq_service.py)

**KEVIN** (formerly JARVIS) is an elite, tech-centric AI partner designed for **AS**. He is more than an assistant—he is a collaborator, system controller, and digital protector.

---

## ⚡ Core Intelligence Features

### 🧠 Neural Hand Interface
- **Neural Mouse (Middle Pinch)**: Control your system mouse using hand movement. Includes an 'Air Tap' (quick thrust) to click and vertical hand-shifts for scrolling.
- **Air Writing (Index Pinch)**: Write commands directly in the air. Kevin uses integrated **Tesseract.js OCR** to transcribe your handwriting and execute system actions.
- **Snappy Response**: Zero-lag tracking with a custom jitter filtration system.

### 💂 Persona & Bilingual Support
- **Witty Defender**: Sharp, protective, and elite persona. 
- **Language Fluidity**: Seamless transitions between English, Hindi, and Hinglish.

### 👁️ Hacker HUD v5.0
- **Clean Dark Theme**: Deep-black grids, scanlines, and neon cyan accents.
- **Vision Feed**: Real-time MediaPipe hand tracking overlaid with a technical skeleton.
- **Performance Telemetry**: Active monitoring of CPU and RAM load.

---

## 🛠️ Technology Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JS, MediaPipe, Tesseract.js
- **LLM**: Meta Llama 3.1 8B (via Groq Cloud)
- **OS Interface**: PyAutoGUI, AppOpener, Psutil
- **Real-time**: WebSockets (Parallelized Gesture Queue)

---

## 🚀 Installation & Setup

1. **Clone the Hub**
   ```bash
   git clone https://github.com/kevin1021-star/KEVIN-My_Assisstant.git
   cd KEVIN-My_Assisstant
   ```

2. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_key_here
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Boot the System**
   ```bash
   python run.py
   ```

---

## 🎮 How to Interact

| Gesture | Mode | Result |
| :--- | :--- | :--- |
| **Index + Thumb Pinch** | `AIR_WRITE` | Draw text in the air. Release to execute as a command. |
| **Middle + Thumb Pinch** | `NEURAL_MOUSE` | Move hand to move cursor. Up/Down to scroll. |
| **Index Forward Thrust** | `AIR_TAP` | Left-Click at current cursor position. |
| **Voice Command** | `COMMS` | Talk naturally to Kevin (Greetings or System Tasks). |

---

> "Logic is just the beginning of wisdom, AS. Let's build something better." — Kevin

---
*Created with ❤️ by AS ."
