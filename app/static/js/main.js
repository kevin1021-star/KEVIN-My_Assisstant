// KEVIN // Advanced Vision & Interface Engine

// -- WEBSOCKET SETUP --
const ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
const chatLog = document.getElementById('chat-log');
const coreOrb = document.getElementById('core-orb');
const statusIndicator = document.querySelector('.status-indicator');

// -- AIR WRITING SETUP --
const airCanvas = document.getElementById('air-canvas');
const airCtx = airCanvas.getContext('2d');
let isWriting = false;
let lastPoint = null;

// -- GESTURE STATE --
let currentMode = 'NONE'; // 'NONE', 'WRITING', 'MOUSE'
const modeTags = {
    WRITING: document.getElementById('mode-writing'),
    MOUSE: document.getElementById('mode-mouse')
};

// -- NEURAL MOUSE TUNING --
let lastMousePos = { x: 0.5, y: 0.5 };
const smoothing = 0.2; // 0.2 = Very Snappy (User request)
let lastSentTime = 0;
const sendIntervalMs = 50; // Throttle to 20fps for reliability

// -- TAP DETECTION (OPTION B) --
let lastIndexZ = 0;
let tapCooldown = 0;

// -- SPEECH RECOGNITION --
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
let isListening = false;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        const transcript = event.results[event.resultIndex][0].transcript;
        appendMessage('user', transcript);
        if(ws.readyState === WebSocket.OPEN) ws.send(transcript);
    };

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('start-btn').classList.add('active');
        coreOrb.classList.add('listening');
    };

    recognition.onend = () => {
        if(isListening) recognition.start();
        else {
            coreOrb.classList.remove('listening');
            document.getElementById('start-btn').classList.remove('active');
        }
    };
}

document.getElementById('start-btn').addEventListener('click', () => {
    if(!recognition) return;
    if(isListening) { isListening = false; recognition.stop(); }
    else recognition.start();
});


// -- WEBSOCKET HANDLING --
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'telemetry') {
        updateBar('cpu-bar', data.cpu);
        updateBar('ram-bar', data.ram);
    } 
    else if (data.type === 'status') {
        coreOrb.className = "core-orb processing";
    } 
    else if (data.type === 'response' || data.type === 'alert') {
        coreOrb.className = "core-orb";
        appendMessage('bot', data.message);
        speakText(data.message);
    }
};

function appendMessage(sender, text) {
    const div = document.createElement('div');
    const label = sender === 'bot' ? 'KEVIN' : (sender === 'user' ? 'AS' : 'SYSTEM');
    div.className = `message ${sender}-msg`;
    div.innerHTML = `<strong>${label} //</strong> ${text}`;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function speakText(text) {
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.pitch = 1.1; utterance.rate = 1.05;
    synth.speak(utterance);
}

// -- MEDIAPIPE HANDS ENGINE --
const videoElement = document.getElementById('webcam');
const canvasElement = document.getElementById('gesture-canvas');
const canvasCtx = canvasElement.getContext('2d');

const hands = new Hands({locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`});
hands.setOptions({ maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.7, minTrackingConfidence: 0.7 });
hands.onResults(onHandResults);

const camera = new Camera(videoElement, {
  onFrame: async () => { await hands.send({image: videoElement}); },
  width: 640, height: 480
});
camera.start();

function onHandResults(results) {
    // Resize canvases to match UI
    [canvasElement, airCanvas].forEach(c => {
        if (c.width !== c.clientWidth || c.height !== c.clientHeight) {
            c.width = c.clientWidth; c.height = c.clientHeight;
        }
    });

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];
        
        // Render techy skeleton
        drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00f3ff', lineWidth: 1});
        drawLandmarks(canvasCtx, landmarks, {color: '#ff003c', radius: 1});

        processGestures(landmarks);
    } else {
        updateMode('NONE');
        lastPoint = null;
    }
    canvasCtx.restore();
}

function processGestures(lm) {
    // Pinch Detectors (Thumb Tip: 4, Index Tip: 8, Middle Tip: 12)
    const indexPinchDist = Math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y);
    const middlePinchDist = Math.hypot(lm[4].x - lm[12].x, lm[4].y - lm[12].y);
    const threshold = 0.05;

    if (indexPinchDist < threshold) {
        updateMode('WRITING');
        handleAirWriting(lm[8]);
    } else if (middlePinchDist < threshold) {
        updateMode('MOUSE');
        handleNeuralMouse(lm[12], lm[8]); // Middle for move, Index for tap detection
    } else {
        updateMode('NONE');
        lastPoint = null;
    }
}

function updateMode(mode) {
    if (currentMode === mode) return;
    
    // If we were writing and just stopped, process the script
    if (currentMode === 'WRITING') {
        processAirScript();
    }

    currentMode = mode;
    Object.keys(modeTags).forEach(k => modeTags[k].classList.remove('active'));
    if (modeTags[mode]) modeTags[mode].classList.add('active');
}

async function processAirScript() {
    const scriptTag = modeTags['WRITING'];
    scriptTag.textContent = "ANALYZING...";
    scriptTag.classList.add('active');

    try {
        // Create an OCR-friendly version (Black on White)
        const ocrCanvas = document.createElement('canvas');
        ocrCanvas.width = airCanvas.width;
        ocrCanvas.height = airCanvas.height;
        const ocrCtx = ocrCanvas.getContext('2d');
        
        // 1. White Background
        ocrCtx.fillStyle = 'white';
        ocrCtx.fillRect(0, 0, ocrCanvas.width, ocrCanvas.height);
        
        // 2. Invert lines to Black
        ocrCtx.globalCompositeOperation = 'difference';
        ocrCtx.drawImage(airCanvas, 0, 0);
        
        // 3. Simple thresholding if needed (optional)
        
        // Run OCR
        const { data: { text } } = await Tesseract.recognize(ocrCanvas, 'eng');
        const cleanText = text.trim().replace(/\n/g, ' ');
        
        if (cleanText.length > 1) {
            appendMessage('system', `DETECTION: "${cleanText}"`);
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(cleanText);
            }
        }
    } catch (e) {
        console.error("OCR Error:", e);
    } finally {
        scriptTag.textContent = "AIR_WRITE";
        airCtx.clearRect(0, 0, airCanvas.width, airCanvas.height);
        lastPoint = null;
    }
}

function handleAirWriting(point) {
    const x = point.x * airCanvas.width;
    const y = point.y * airCanvas.height;

    if (lastPoint) {
        airCtx.beginPath();
        airCtx.strokeStyle = '#00f3ff';
        airCtx.lineWidth = 3;
        airCtx.lineCap = 'round';
        airCtx.moveTo(lastPoint.x, lastPoint.y);
        airCtx.lineTo(x, y);
        airCtx.stroke();
    }
    lastPoint = { x, y };
}

function handleNeuralMouse(controlPoint, indexPoint) {
    const now = Date.now();
    
    // Smooth movement
    lastMousePos.x = lastMousePos.x * smoothing + controlPoint.x * (1 - smoothing);
    lastMousePos.y = lastMousePos.y * smoothing + controlPoint.y * (1 - smoothing);

    // Tap Detection (Option B) - Detection of sudden 'thrust' in Z-axis
    let click = false;
    const zDelta = lastIndexZ - indexPoint.z;
    if (zDelta > 0.06 && tapCooldown <= 0) {
        click = true;
        tapCooldown = 8;
        triggerUIFlash();
    }
    lastIndexZ = indexPoint.z;
    if (tapCooldown > 0) tapCooldown--;

    // Send to Backend (Throttled)
    if (ws.readyState === WebSocket.OPEN && (now - lastSentTime > sendIntervalMs || click)) {
        ws.send(JSON.stringify({
            type: 'gesture_sync',
            mode: 'MOUSE',
            x: lastMousePos.x,
            y: lastMousePos.y,
            click: click
        }));
        lastSentTime = now;
    }
}

function triggerUIFlash() {
    coreOrb.style.boxShadow = '0 0 50px #ff003c';
    setTimeout(() => { coreOrb.style.boxShadow = ''; }, 100);
}

function updateBar(id, value) {
    const bar = document.getElementById(id);
    if (bar) bar.style.width = `${value}%`;
}

// Clock 
setInterval(() => {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('en-US', {hour12: false});
}, 1000);
