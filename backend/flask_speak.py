from flask import Flask, request, jsonify
from flask_cors import CORS
import os, time, base64, threading, requests, pygame
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('SARVAM_API_KEY')
if not API_KEY:
    raise SystemExit("SARVAM_API_KEY missing in .env")

pygame.mixer.init()
app = Flask(__name__)

# 👇 Allow Chrome to POST requests from any site
CORS(app, resources={r"/speak": {"origins": "*"}}, supports_credentials=True)

# 👇 Add globals
last_spoken = ""
last_time = 0
COOLDOWN = 0.8  # seconds between announcements

def speak_text(text):
    global last_spoken, last_time
    now = time.time()
    if text == last_spoken or now - last_time < COOLDOWN:
        return
    last_spoken, last_time = text, now

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "API-Subscription-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text],
        "target_language_code": "en-IN",
        "speaker": "manisha",
        "pitch": 0,
        "pace": 1.0,
        "loudness": 1.0,
        "speech_sample_rate": 8000,
        "enable_preprocessing": True,
        "model": "bulbul:v2"
    }

    try:
        print(f"Requesting TTS for: {text}")
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status code: {r.status_code}")
        print(f"Response text: {r.text[:100]}...")
        r.raise_for_status()

        data = r.json()
        audio_b64 = data['audios'][0]
        print(f"Audio base64 length: {len(audio_b64)}")

        audio = base64.b64decode(audio_b64)
        print(f"Decoded audio length: {len(audio)} bytes")

        with open("speak.wav", "wb") as f:
            f.write(audio)
        print("Audio written to speak.wav")

        pygame.mixer.music.load("speak.wav")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        os.remove("speak.wav")

        print("Playback done ✅")

    except Exception as e:
        print("TTS Error:", e)

@app.route("/speak", methods=["POST"])
def speak():
    """Receive text from extension and play TTS"""
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "msg": "No text"}), 400

    threading.Thread(target=speak_text, args=(text,), daemon=True).start()
    return jsonify({"ok": True})

# 👇 This ensures CORS headers are added for all responses
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

if __name__ == "__main__":
    app.run(port=5000)
