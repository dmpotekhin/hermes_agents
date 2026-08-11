# Web Speech API for Voice Input

Browser-native speech-to-text with zero dependencies. Works in Chrome and Safari.

## HTML — Mic Button

```html
<button id="mic-btn" onclick="toggleMic()" title="Голосовой ввод">🎤</button>
```

## CSS — Listening Indicator

```css
#mic-btn.listening { background: #e74c3c; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
```

## JS — Recognition + Auto-Send

```javascript
let recognition = null;

function initSpeech() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;  // unsupported browser
  recognition = new SpeechRecognition();
  recognition.lang = 'ru-RU';
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    document.getElementById('chat-input').value = text;
    stopMic();
    sendChat();  // auto-send after recognition
  };
  recognition.onerror = () => stopMic();
  recognition.onend = () => stopMic();
}

function toggleMic() {
  if (!recognition) { initSpeech(); if (!recognition) return alert('Not supported'); }
  const btn = document.getElementById('mic-btn');
  if (btn.classList.contains('listening')) { recognition.stop(); return; }
  btn.classList.add('listening');
  btn.textContent = '🔴';
  recognition.start();
}

function stopMic() {
  const btn = document.getElementById('mic-btn');
  btn.classList.remove('listening');
  btn.textContent = '🎤';
}
```

## Key Points

- Lazy-init on first click — no mic permission prompt on page load
- `lang='ru-RU'` for Russian — change to `'en-US'` etc. as needed
- Auto-sends after recognition (calls `sendChat()`)
- Red pulsing button while listening, back to 🎤 when done
- `recognition.onend` fires even on error — ensures button resets
