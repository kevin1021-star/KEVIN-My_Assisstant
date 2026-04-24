// KEVIN HUD v2 - Intelligence Integration
const chatInput = document.getElementById("chat-input");
const micButton = document.getElementById("mic-btn");
const speakToggle = document.getElementById("speak-toggle");
const connectionPill = document.getElementById("connection-pill");
const modeBadge = document.getElementById("mode-badge");
const visionState = document.getElementById("vision-state");
const neuralLog = document.getElementById("neural-log");

const gestureCanvas = document.getElementById("gesture-canvas");
const videoElement = document.getElementById("webcam");
const gestureCtx = gestureCanvas.getContext("2d");

// Initialize HUD Components
const cpuGauge = new HUD.CircularGauge("cpu-gauge-v2", "CPU_LOAD", "var(--accent)");
const memGauge = new HUD.CircularGauge("mem-gauge-v2", "MEM_USAGE", "var(--secondary)");
const feed = new HUD.IntelligenceFeed("chat-log");

// Global State
let speakResponses = true;
let isListening = false;
let recognition = null;
let socket = null;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

// Initialize Mermaid
mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });

// Initialization Boot Sequence
async function bootSequence() {
    log("Initializing Neural OS...");
    await new Promise(r => setTimeout(r, 500));
    log("Loading Core Modules...");
    await new Promise(r => setTimeout(r, 400));
    log("Establishing Secure Link...");
    initSocket();
    await new Promise(r => setTimeout(r, 600));
    log("Vision Systems Online");
    log("System Ready");
}

function log(msg) {
    if (neuralLog) {
        const line = document.createElement("div");
        line.textContent = `> ${msg.toUpperCase()}`;
        neuralLog.prepend(line);
        if (neuralLog.childNodes.length > 10) neuralLog.lastChild.remove();
    }
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
            connectionPill.style.color = "var(--accent)";
            connectionPill.classList.add("animate-pulse");
        }
        camera.start().catch(err => log(`Vision Fail: ${err}`));
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "telemetry") {
            cpuGauge.update(data.cpu);
            memGauge.update(data.ram);
        } else if (data.type === "chat") {
            feed.append("assistant", data.content);
            if (speakResponses) speakText(data.content);
            
            // Flowchart detection logic
            if (data.content.includes("```mermaid")) {
                const mermaidMatch = data.content.match(/```mermaid([\s\S]*?)```/);
                if (mermaidMatch && mermaidMatch[1]) {
                    renderFlowchart(mermaidMatch[1].trim());
                }
            }
        }
    };

    async function renderFlowchart(code) {
        const overlay = document.getElementById("flowchart-overlay");
        const renderArea = document.getElementById("flowchart-render");
        
        try {
            log("Rendering tactical plan...");
            const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), code);
            renderArea.innerHTML = svg;
            overlay.style.display = "flex";
            log("Plan displayed");
        } catch (err) {
            log(`Flowchart Error: ${err.message}`);
            console.error(err);
        }
    }

    socket.onclose = () => {
        log("Link Lost. Re-establishing...");
        if (connectionPill) {
            connectionPill.textContent = "LINK_OFFLINE";
            connectionPill.style.color = "var(--alert)";
            connectionPill.classList.remove("animate-pulse");
        }
        setTimeout(initSocket, 3000);
    };
}

function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || !socket || socket.readyState !== WebSocket.OPEN) {
        log("No Link. Message Queued.");
        return;
    }
    feed.append("user", trimmed);
    socket.send(trimmed);
}

// Vision Engine
const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
    maxNumHands: 2,
    modelComplexity: 1,
    minDetectionConfidence: 0.4,
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
        results.multiHandLandmarks.forEach((landmarks) => {
            drawConnectors(gestureCtx, landmarks, HAND_CONNECTIONS, { color: "rgba(0, 242, 255, 0.3)", lineWidth: 1 });
            drawLandmarks(gestureCtx, landmarks, { color: "var(--accent)", lineWidth: 1, radius: 2 });
            
            const thumb = landmarks[4];
            const indexTip = landmarks[8];
            const middleTip = landmarks[12];
            
            const ringTip = landmarks[16];
            const pinkyTip = landmarks[20];
            
            const distIndex = Math.hypot(thumb.x - indexTip.x, thumb.y - indexTip.y);
            const distMiddle = Math.hypot(thumb.x - middleTip.x, thumb.y - middleTip.y);
            const distRing = Math.hypot(thumb.x - ringTip.x, thumb.y - ringTip.y);
            const distPinky = Math.hypot(thumb.x - pinkyTip.x, thumb.y - pinkyTip.y);

            // Three Fingers Up (Summon)
            if (indexTip.y < thumb.y && middleTip.y < thumb.y && ringTip.y < thumb.y && pinkyTip.y > thumb.y) {
                modeBadge.textContent = "SUMMON";
                socket.send("summon partner");
                log("Companion Summoned");
                
                // Automatically activate voice listening
                if (typeof isListening !== 'undefined' && !isListening) {
                    const micBtn = document.getElementById("mic-btn");
                    if (micBtn) micBtn.click();
                }
            } 
            // Fist (Dismiss)
            else if (distIndex < 0.08 && distMiddle < 0.08 && distRing < 0.08 && distPinky < 0.08) {
                modeBadge.textContent = "DISMISS";
                if (window.companionWindow && !window.companionWindow.closed) {
                    window.companionWindow.close();
                    log("Companion Dismissed");
                }
            }
            else if (distMiddle < 0.05) {
                modeBadge.textContent = "POINTER";
                socket.send(JSON.stringify({ type: "gesture", x: middleTip.x, y: middleTip.y, action: "move" }));
            } else if (distIndex < 0.05) {
                log("Click Gesture");
                socket.send(JSON.stringify({ type: "gesture", x: indexTip.x, y: indexTip.y, action: "click" }));
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
        micButton.style.background = "var(--accent)";
        micButton.style.color = "var(--bg-dark)";
        log("Mic Active");
    };

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        log(`Heard: ${text}`);
        sendMessage(text);
    };

    recognition.onend = () => {
        isListening = false;
        micButton.style.background = "";
        micButton.style.color = "";
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
    speakToggle.textContent = speakResponses ? "VOICE: ACTIVE" : "VOICE: MUTED";
    speakToggle.style.borderColor = speakResponses ? "var(--accent)" : "var(--alert)";
};

bootSequence();
setInterval(syncClock, 1000);
syncClock();
