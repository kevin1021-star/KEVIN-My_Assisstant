// J.A.R.V.I.S Core Frontend Logic

// -- WEBSOCKET SETUP --
const ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
const chatLog = document.getElementById('chat-log');
const coreOrb = document.getElementById('core-orb');
const statusIndicator = document.querySelector('.status-indicator');
const voiceStatusText = document.getElementById('voice-status');

// -- SPEECH RECOGNITION SETUP --
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
let isListening = false;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true; // Keep listening until explicitly stopped
    recognition.interimResults = false;
    
    // Set initial language
    recognition.lang = document.querySelector('input[name="lang"]:checked').value;

    recognition.onstart = function() {
        isListening = true;
        document.getElementById('start-btn').textContent = "DEACTIVATE MIC";
        document.getElementById('start-btn').classList.add('active');
        coreOrb.classList.add('listening');
        voiceStatusText.textContent = "Listening...";
    };

    recognition.onresult = function(event) {
        const current = event.resultIndex;
        const transcript = event.results[current][0].transcript;
        
        // Display User Message
        appendMessage('user', transcript);
        
        // Send to FastAPI over WebSocket
        if(ws.readyState === WebSocket.OPEN) {
            ws.send(transcript);
            voiceStatusText.textContent = "Transmitting...";
        }
    };

    recognition.onerror = function(event) {
        console.error("Speech Recognition Error", event.error);
        if(event.error === 'no-speech') {
            // Ignore silence
        } else {
            stopListening();
        }
    };

    recognition.onend = function() {
        if(isListening) {
            // Auto-restart if we didn't manually stop it
            recognition.start();
        } else {
            coreOrb.className = "core-orb";
            document.getElementById('start-btn').textContent = "ENGAGE MICROPHONE";
            document.getElementById('start-btn').classList.remove('active');
            voiceStatusText.textContent = "Standby.";
        }
    };
} else {
    alert("Speech Recognition API is not supported in this browser. Please use Chrome or Edge.");
}


// -- EVENT LISTENERS --

// Mic Toggle
document.getElementById('start-btn').addEventListener('click', () => {
    if(!recognition) return;
    
    if(isListening) {
        stopListening();
    } else {
        recognition.start();
    }
});

// Language Toggle
const langRadios = document.querySelectorAll('input[name="lang"]');
langRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if(recognition) {
            recognition.lang = e.target.value;
            // Need to restart recognition to apply language change
            if(isListening) {
                recognition.stop(); 
                // onend will automatically restart it with the new lang
            }
        }
    });
});

function stopListening() {
    isListening = false;
    recognition.stop();
}


// -- WEBSOCKET HANDLING --
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'telemetry') {
        updateBar('cpu-bar', data.cpu);
        updateBar('ram-bar', data.ram);
        updateBar('battery-bar', data.battery);
    } 
    else if (data.type === 'alert') {
        // Kevin is being proactive!
        appendMessage('bot', data.message);
        speakText(data.message, document.querySelector('input[name="lang"]:checked').value);
    }
    else if (data.type === 'status') {
        // AI is thinking
        coreOrb.className = "core-orb processing";
        statusIndicator.className = "status-indicator processing";
        voiceStatusText.textContent = "JARVIS is forming a response...";
    } 
    else if (data.type === 'response') {
        // AI responded
        coreOrb.className = "core-orb listening"; // Go back to listen animation
        statusIndicator.className = "status-indicator online";
        voiceStatusText.textContent = "Listening...";
        appendMessage('bot', data.message);
        
        // Make JARVIS speak out loud!
        speakText(data.message, document.querySelector('input[name="lang"]:checked').value);
    }
};

ws.onclose = () => {
    appendMessage('system', 'Connection lost to Core Server.');
    statusIndicator.className = "status-indicator";
    statusIndicator.style.backgroundColor = "red";
}


// -- HELPER FUNCTIONS --
function appendMessage(sender, text) {
    const div = document.createElement('div');
    const label = sender === 'bot' ? 'KEVIN' : (sender === 'user' ? 'AS' : 'SYSTEM');
    div.className = `message ${sender}-msg`;
    div.innerHTML = `<strong>${label}:</strong> ${text}`;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function speakText(text, lang) {
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Find an Indian Male voice if possible
    const voices = synth.getVoices();
    let bestVoice = voices.find(v => (v.lang === 'en-IN' || v.lang ==='hi-IN') && v.name.toLowerCase().includes('male'));
    if (!bestVoice) bestVoice = voices.find(v => v.lang === 'en-IN' || v.lang === 'hi-IN');
    if (!bestVoice) bestVoice = voices.find(v => v.name.toLowerCase().includes('male'));
    
    if (bestVoice) utterance.voice = bestVoice;
    utterance.lang = lang; 
    
    // Kevin's Persona traits
    utterance.pitch = 1.1; // Slightly higher for a younger boyish feel
    utterance.rate = 1.05; // Slightly faster for wit
    
    // Don't listen to ourselves talking
    if(isListening) { recognition.stop(); }
    
    utterance.onend = () => {
        if(isListening) { recognition.start(); }
    };
    
    synth.speak(utterance);
}

// -- MEDIAPIPE HANDS SETUP --
const videoElement = document.getElementById('webcam');
const canvasElement = document.getElementById('gesture-canvas');
const canvasCtx = canvasElement.getContext('2d');
const visionStatus = document.getElementById('vision-status');

const hands = new Hands({locateFile: (file) => {
  return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
}});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.7
});

hands.onResults(onHandResults);

const camera = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({image: videoElement});
  },
  width: 640,
  height: 480
});
camera.start().then(() => {
    visionStatus.textContent = "Vision Sensor Online";
    visionStatus.classList.remove('blink');
});

function onHandResults(results) {
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  
  // Set canvas size to match display size for perfect alignment
  if (canvasElement.width !== canvasElement.clientWidth || canvasElement.height !== canvasElement.clientHeight) {
      canvasElement.width = canvasElement.clientWidth;
      canvasElement.height = canvasElement.clientHeight;
  }

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const landmarks = results.multiHandLandmarks[0];
    
    // Draw landmarks for tech look
    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00f3ff', lineWidth: 2});
    drawLandmarks(canvasCtx, landmarks, {color: '#ff003c', lineWidth: 1, radius: 2});

    // Detect Gestures
    detectGestures(landmarks);
  }
  canvasCtx.restore();
}

function detectGestures(landmarks) {
    // Basic logic: Open Palm (all fingers up) vs Fist (all fingers down)
    const isFist = isFingerDown(landmarks, 8) && isFingerDown(landmarks, 12) && isFingerDown(landmarks, 16) && isFingerDown(landmarks, 20);
    const isOpenPalm = !isFingerDown(landmarks, 8) && !isFingerDown(landmarks, 12) && !isFingerDown(landmarks, 16) && !isFingerDown(landmarks, 20);

    if (isOpenPalm) {
        // Stop JARVIS from talking
        const synth = window.speechSynthesis;
        if (synth.speaking) {
            synth.cancel();
            voiceStatusText.textContent = "Synthesizer Silenced by Gesture.";
        }
    }
}

function isFingerDown(landmarks, tipIdx) {
    // Simple check: is the tip below the pip joint? (In MediaPipe Y decreases as you go up)
    return landmarks[tipIdx].y > landmarks[tipIdx - 2].y;
}

function updateBar(id, value) {
    const bar = document.getElementById(id);
    if (!bar) return;
    bar.style.width = `${value}%`;
    
    // Change colors based on load
    bar.classList.remove('warning', 'danger');
    if (value > 85) {
        bar.classList.add('danger');
    } else if (value > 60) {
        bar.classList.add('warning');
    }
}

// Clock 
setInterval(() => {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('en-US', {hour12: false});
}, 1000);
