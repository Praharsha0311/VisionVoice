import cv2
import os
import time
import threading
import requests
import pygame
import base64
from dotenv import load_dotenv
from ultralytics import YOLO

load_dotenv()
api_key = os.getenv('SARVAM_API_KEY')
if not api_key:
    print("SARVAM_API_KEY not found in .env")
    exit(1)

pygame.mixer.init()

hazardous_objects = ['knife', 'scissors', 'gun', 'fire']
last_announced = 0
announce_cooldown = 3

def play_tts(text):
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "API-Subscription-Key": api_key,
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
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            audio_base64 = data['audios'][0]
            audio_data = base64.b64decode(audio_base64)
            with open('temp_audio.wav', 'wb') as f:
                f.write(audio_data)
            pygame.mixer.music.load('temp_audio.wav')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.stop()
            pygame.mixer.music.unload()   # <-- important
            os.remove('temp_audio.wav')

        else:
            print(f"TTS failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"TTS error: {e}")

model = YOLO("yolo11n.pt")

def generate_frames():
    global last_announced
    camera = cv2.VideoCapture(0)
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        results = model(frame, verbose=False)
        detections = results[0].boxes
        detected_hazardous = []
        plot_frame = frame.copy()
        for box in detections:
            cls = int(box.cls[0])
            class_name = model.names[cls]
            x1, y1, x2, y2 = box.xyxy[0]
            conf = box.conf[0]
            if class_name in hazardous_objects:
                color = (0, 0, 255)  # red
                detected_hazardous.append(class_name)
            else:
                color = (0, 255, 0)  # green
            cv2.rectangle(plot_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(plot_frame, f"{class_name} {conf:.2f}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        if detected_hazardous and time.time() - last_announced > announce_cooldown:
            unique_hazards = list(set(detected_hazardous))
            for hazard in unique_hazards:
                text = f"{hazard} detected, be cautious"
                threading.Thread(target=play_tts, args=(text,)).start()
            last_announced = time.time()
        ret, buffer = cv2.imencode('.jpg', plot_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    camera.release()
