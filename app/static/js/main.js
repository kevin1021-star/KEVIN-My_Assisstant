const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const micButton = document.getElementById("mic-btn");
const speakToggle = document.getElementById("speak-toggle");
const connectionPill = document.getElementById("connection-pill");
const heroStatus = document.getElementById("hero-status");
const heroDetail = document.getElementById("hero-detail");
const cpuBar = document.getElementById("cpu-bar");
const ramBar = document.getElementById("ram-bar");
const cpuValue = document.getElementById("cpu-value");
const ramValue = document.getElementById("ram-value");
const modeValue = document.getElementById("mode-value");
const modeBadge = document.getElementById("mode-badge");
const featureValue = document.getElementById("feature-value");
const visionState = document.getElementById("vision-state");

const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws/chat`);

let speakResponses = false;
let isListening = false;
let currentMode = "IDLE";
let lastPoint = null;
let lastMousePos = { x: 0.5, y: 0.5 };
let lastSentTime = 0;
let lastIndexZ = 0;
let tapCooldown = 0;

const airCanvas = document.getElementById("air-canvas");
const gestureCanvas = document.getElementById("gesture-canvas");
const videoElement = document.getElementById("webcam");
const airCtx = airCanvas.getContext("2d");
const gestureCtx = gestureCanvas.getContext("2d");
const sendIntervalMs = 50;
const smoothing = 0.2;

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

function syncClock() {
    document.getElementById("clock").textContent = new Date().toLocaleTimeString("en-IN", { hour12: false });
}

function setConnectionState(label, connected) {
    connectionPill.textContent = label;
    connectionPill.classList.toggle("online", connected);
    connectionPill.classList.toggle("offline", !connected);
}

function appendMessage(role, text) {
    const card = document.createElement("article");
    card.className = `message ${role}`;
    card.innerHTML = `<span class="message-role">${role.toUpperCase()}</span><p></p>`;
    card.querySelector("p").textContent = text;
    chatLog.appendChild(card);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || socket.readyState !== WebSocket.OPEN) {
        return;
    }

    appendMessage("user", trimmed);
    socket.send(trimmed);
    heroStatus.textContent = "Working on your request";
    heroDetail.textContent = trimmed;
}

function updateTelemetry(cpu, ram) {
    cpuValue.textContent = `${cpu}%`;
    ramValue.textContent = `${ram}%`;
    cpuBar.style.width = `${cpu}%`;
    ramBar.style.width = `${ram}%`;
}

function updateMode(mode) {
    if (currentMode === "AIR_WRITE" && mode !== "AIR_WRITE") {
        processAirScript();
    }

    currentMode = mode;
    modeValue.textContent = mode.replace("_", " ");
    modeBadge.textContent = mode;
}

function speakText(text) {
    if (!speakResponses || !window.speechSynthesis) {
        return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.02;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
}

socket.addEventListener("open", () => {
    setConnectionState("Connected", true);
    heroStatus.textContent = "Ready for commands";
    heroDetail.textContent = "Use text, voice, or gestures to interact.";
});

socket.addEventListener("close", () => {
    setConnectionState("Disconnected", false);
    heroStatus.textContent = "Connection closed";
    heroDetail.textContent = "Refresh the page to reconnect.";
});

socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "telemetry") {
        updateTelemetry(data.cpu, data.ram);
        return;
    }

    if (data.type === "status") {
        heroStatus.textContent = "Processing";
        heroDetail.textContent = data.message;
        return;
    }

    if (data.type === "response" || data.type === "alert") {
        appendMessage("assistant", data.message);
        heroStatus.textContent = data.type === "alert" ? "Attention needed" : "Response ready";
        heroDetail.textContent = data.message;
        featureValue.textContent = data.type === "alert" ? "Alert mode" : "Chat Ready";
        speakText(data.message);
    }
});

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(chatInput.value);
    chatInput.value = "";
});

document.querySelectorAll(".quick-action").forEach((button) => {
    button.addEventListener("click", () => sendMessage(button.dataset.message || ""));
});

speakToggle.addEventListener("click", () => {
    speakResponses = !speakResponses;
    speakToggle.textContent = speakResponses ? "Voice On" : "Voice Off";
});

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
        isListening = true;
        micButton.textContent = "Stop Voice";
        heroStatus.textContent = "Listening";
        heroDetail.textContent = "Speech recognition is active.";
    };

    recognition.onend = () => {
        if (isListening) {
            recognition.start();
            return;
        }
        micButton.textContent = "Start Voice";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[event.resultIndex][0].transcript;
        sendMessage(transcript);
    };

    micButton.addEventListener("click", () => {
        if (isListening) {
            isListening = false;
            recognition.stop();
            return;
        }
        recognition.start();
    });
} else {
    micButton.disabled = true;
    micButton.textContent = "Voice Unsupported";
}

function resizeVisionCanvases() {
    const width = gestureCanvas.clientWidth;
    const height = gestureCanvas.clientHeight;
    if (!width || !height) {
        return;
    }

    [gestureCanvas, airCanvas].forEach((canvas) => {
        if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
        }
    });
}

function handleAirWriting(point) {
    const x = point.x * airCanvas.width;
    const y = point.y * airCanvas.height;

    if (lastPoint) {
        airCtx.beginPath();
        airCtx.strokeStyle = "#8bf7d4";
        airCtx.lineWidth = 4;
        airCtx.lineCap = "round";
        airCtx.moveTo(lastPoint.x, lastPoint.y);
        airCtx.lineTo(x, y);
        airCtx.stroke();
    }

    lastPoint = { x, y };
}

function handleNeuralMouse(controlPoint, indexPoint) {
    const now = Date.now();
    lastMousePos.x = lastMousePos.x * smoothing + controlPoint.x * (1 - smoothing);
    lastMousePos.y = lastMousePos.y * smoothing + controlPoint.y * (1 - smoothing);

    let click = false;
    const zDelta = lastIndexZ - indexPoint.z;
    if (zDelta > 0.06 && tapCooldown <= 0) {
        click = true;
        tapCooldown = 8;
    }

    lastIndexZ = indexPoint.z;
    if (tapCooldown > 0) {
        tapCooldown -= 1;
    }

    if (socket.readyState === WebSocket.OPEN && (now - lastSentTime > sendIntervalMs || click)) {
        socket.send(JSON.stringify({
            type: "gesture_sync",
            mode: "MOUSE",
            x: lastMousePos.x,
            y: lastMousePos.y,
            click,
        }));
        lastSentTime = now;
    }
}

async function processAirScript() {
    if (!lastPoint) {
        return;
    }

    heroStatus.textContent = "Reading air script";
    heroDetail.textContent = "Running OCR on your gesture strokes.";

    try {
        const ocrCanvas = document.createElement("canvas");
        ocrCanvas.width = airCanvas.width;
        ocrCanvas.height = airCanvas.height;
        const ocrCtx = ocrCanvas.getContext("2d");
        ocrCtx.fillStyle = "white";
        ocrCtx.fillRect(0, 0, ocrCanvas.width, ocrCanvas.height);
        ocrCtx.globalCompositeOperation = "difference";
        ocrCtx.drawImage(airCanvas, 0, 0);

        const result = await Tesseract.recognize(ocrCanvas, "eng");
        const cleanText = result.data.text.trim().replace(/\n/g, " ");
        if (cleanText.length > 1) {
            sendMessage(cleanText);
        }
    } catch (error) {
        appendMessage("system", `OCR failed: ${error}`);
    } finally {
        airCtx.clearRect(0, 0, airCanvas.width, airCanvas.height);
        lastPoint = null;
    }
}

function initVision() {
    if (!window.Hands || !window.Camera) {
        visionState.textContent = "Vision libraries unavailable";
        return;
    }

    resizeVisionCanvases();
    window.addEventListener("resize", resizeVisionCanvases);

    const hands = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
    });

    hands.setOptions({
        maxNumHands: 1,
        modelComplexity: 1,
        minDetectionConfidence: 0.7,
        minTrackingConfidence: 0.7,
    });

    hands.onResults((results) => {
        resizeVisionCanvases();
        gestureCtx.save();
        gestureCtx.clearRect(0, 0, gestureCanvas.width, gestureCanvas.height);

        if (results.multiHandLandmarks && results.multiHandLandmarks.length) {
            const lm = results.multiHandLandmarks[0];
            drawConnectors(gestureCtx, lm, HAND_CONNECTIONS, { color: "#7dd3fc", lineWidth: 2 });
            drawLandmarks(gestureCtx, lm, { color: "#f97316", lineWidth: 1, radius: 2 });

            const indexPinchDist = Math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y);
            const middlePinchDist = Math.hypot(lm[4].x - lm[12].x, lm[4].y - lm[12].y);

            if (indexPinchDist < 0.05) {
                updateMode("AIR_WRITE");
                handleAirWriting(lm[8]);
            } else if (middlePinchDist < 0.05) {
                updateMode("NEURAL_MOUSE");
                handleNeuralMouse(lm[12], lm[8]);
            } else {
                updateMode("IDLE");
                lastPoint = null;
            }
            visionState.textContent = "Camera active";
        } else {
            updateMode("IDLE");
            visionState.textContent = "Hand not detected";
        }

        gestureCtx.restore();
    });

    const camera = new Camera(videoElement, {
        onFrame: async () => hands.send({ image: videoElement }),
        width: 640,
        height: 480,
    });

    camera.start().catch((error) => {
        visionState.textContent = `Camera blocked: ${error}`;
    });
}

syncClock();
setInterval(syncClock, 1000);
initVision();
