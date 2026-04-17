const chatLog = document.getElementById("chat-log");
const chatInput = document.getElementById("chat-input");
const micButton = document.getElementById("mic-btn");
const speakToggle = document.getElementById("speak-toggle");
const connectionPill = document.getElementById("connection-pill");
const cpuValue = document.getElementById("cpu-value");
const memValue = document.getElementById("mem-value");
const cpuGauge = document.getElementById("cpu-gauge");
const memGauge = document.getElementById("mem-gauge");
const modeBadge = document.getElementById("mode-badge");
const visionState = document.getElementById("vision-state");
const neuralLog = document.getElementById("neural-log");

const gestureCanvas = document.getElementById("gesture-canvas");
const videoElement = document.getElementById("webcam");
const gestureCtx = gestureCanvas.getContext("2d");

let speakResponses = true;
let isListening = false;
let recognition = null;
let currentMode = "IDLE";
let socket = null;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function log(msg) {
    if (neuralLog) neuralLog.textContent = msg.toUpperCase();
    console.log(`[KEVIN] ${msg}`);
}

function syncClock() {
    document.getElementById("clock").textContent = new Date().toLocaleTimeString("en-IN", { hour12: false });
}

function initSocket() {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws/chat`);

    socket.onopen = () => {
        log("Neural Link Established");
        if (connectionPill) {
            connectionPill.textContent = "LINK_ACTIVE";
            connectionPill.style.color = "var(--cyan)";
        }
        camera.start().catch(err => log(`Vision Fail: ${err}`));
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "telemetry") updateTelemetry(data.cpu, data.ram);
        else if (data.type === "chat") {
            appendMessage("assistant", data.content);
            if (speakResponses) speakText(data.content);
        }
    };

    socket.onclose = () => {
        log("Link Lost. Re-establishing...");
        if (connectionPill) {
            connectionPill.textContent = "LINK_OFFLINE";
            connectionPill.style.color = "var(--alert)";
        }
        setTimeout(initSocket, 3000);
    };
}

function appendMessage(role, text) {
    const msg = document.createElement("div");
    msg.className = `msg ${role}`;
    msg.innerHTML = `<span class="role">${role.toUpperCase()}</span><p>${text}</p>`;
    chatLog.appendChild(msg);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || !socket || socket.readyState !== WebSocket.OPEN) {
        log("No Link. Message Queued.");
        return;
    }
    appendMessage("user", trimmed);
    socket.send(trimmed);
}

function updateTelemetry(cpu, ram) {
    if (cpuValue) cpuValue.textContent = `${cpu}%`;
    if (memValue) memValue.textContent = `${ram}%`;
    const circ = 283; 
    if (cpuGauge) cpuGauge.style.strokeDashoffset = circ - (cpu / 100) * circ;
    if (memGauge) memGauge.style.strokeDashoffset = circ - (ram / 100) * circ;
}

// Vision Engine
const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
    maxNumHands: 2,
    modelComplexity: 1,
    minDetectionConfidence: 0.4, // Lowered for better sensitivity
    minTrackingConfidence: 0.4,
});

hands.onResults((results) => {
    if (gestureCanvas.width !== videoElement.videoWidth) {
        gestureCanvas.width = videoElement.videoWidth;
        gestureCanvas.height = videoElement.videoHeight;
    }

    gestureCtx.save();
    gestureCtx.clearRect(0, 0, gestureCanvas.width, gestureCanvas.height);
    visionState.textContent = `HANDS_${results.multiHandLandmarks.length}`;

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        results.multiHandLandmarks.forEach((landmarks, index) => {
            drawConnectors(gestureCtx, landmarks, HAND_CONNECTIONS, { color: "rgba(0, 242, 255, 0.5)", lineWidth: 2 });
            drawLandmarks(gestureCtx, landmarks, { color: "var(--cyan)", lineWidth: 1, radius: 2 });
            
            const thumb = landmarks[4];
            const indexTip = landmarks[8];
            const middleTip = landmarks[12];
            
            const distIndex = Math.hypot(thumb.x - indexTip.x, thumb.y - indexTip.y);
            const distMiddle = Math.hypot(thumb.x - middleTip.x, thumb.y - middleTip.y);

            if (distMiddle < 0.05) {
                modeBadge.textContent = "POINTER";
                socket.send(JSON.stringify({ type: "gesture", x: middleTip.x, y: middleTip.y, action: "move" }));
            } else if (distIndex < 0.05) {
                log("Click Detected");
                socket.send(JSON.stringify({ type: "gesture", action: "click" }));
            } else {
                modeBadge.textContent = "IDLE";
            }
        });
    }
    gestureCtx.restore();
});

// Voice Engine
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "en-IN";

    recognition.onstart = () => {
        isListening = true;
        micButton.style.backgroundColor = "var(--cyan)";
        log("Mic Active...");
    };

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        log(`Heard: ${text}`);
        sendMessage(text);
    };

    recognition.onend = () => {
        isListening = false;
        micButton.style.backgroundColor = "";
    };
}

micButton.onclick = () => {
    if (isListening) recognition.stop();
    else recognition.start();
};

const camera = new Camera(videoElement, {
    onFrame: async () => {
        await hands.send({ image: videoElement });
    },
    width: 640,
    height: 480,
});

function speakText(text) {
    if (!speakResponses || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    window.speechSynthesis.speak(utterance);
}

document.getElementById("send-btn").onclick = () => {
    sendMessage(chatInput.value);
    chatInput.value = "";
};

speakToggle.onclick = () => {
    speakResponses = !speakResponses;
    speakToggle.textContent = speakResponses ? "ACTIVE" : "MUTED";
    speakToggle.style.borderColor = speakResponses ? "var(--cyan)" : "var(--alert)";
};

initSocket();
setInterval(syncClock, 1000);
syncClock();
