import cv2
import numpy as np
import threading
import time
from gtts import gTTS
from playsound import playsound
import os

last_instruction = ""
last_spoken_time = 0
speak_cooldown = 1.5  # seconds between speaks

# Predefined encouraging phrases for navigation
encouraging_phrases = [
    "Great job! You're almost there.",
    "Keep going, you're doing fantastic!",
    "Excellent progress! The door is close.",
    "You're navigating like a pro!",
    "Almost at the door! Stay focused.",
    "Wonderful! You're getting closer.",
    "Superb navigation! Door ahead.",
    "You're doing amazing! Keep it up.",
    "Fantastic! The door is within reach.",
    "Brilliant! You're almost there."
]

current_phrase_index = 0

def speak(text):
    global last_spoken_time
    if time.time() - last_spoken_time < speak_cooldown:
        return
    print("Voice:", text)
    tts = gTTS(text=text, lang='en')
    tts.save("voice.mp3")
    playsound("voice.mp3")
    os.remove("voice.mp3")
    last_spoken_time = time.time()

def generate_frames():
    global last_instruction, current_phrase_index
    cap = cv2.VideoCapture(0)  # Change to 1 if using external webcam
    cap.set(3, 640)
    cap.set(4, 480)
    FRAME_CENTER = 640 // 2

    door_not_visible_count = 0
    door_visible_count = 0
    door_previously_visible = False
    previous_max_visible = 0
    max_door_width = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7,7), 0)
        edges = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        biggest_rect = None
        biggest_area = 0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if h > 200 and w > 80:
                aspect_ratio = h / w
                if 1.6 < aspect_ratio < 3.8:
                    area = w * h
                    if area > biggest_area:
                        biggest_area = area
                        biggest_rect = (x, y, w, h)

        if biggest_rect:
            x, y, w, h = biggest_rect
            x_center = x + w // 2

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 3)
            cv2.putText(frame, "DOOR", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,255,0),2)

            door_not_visible_count = 0
            door_visible_count += 1
            previous_max_visible = max(previous_max_visible, door_visible_count)
            max_door_width = max(max_door_width, w)
            door_previously_visible = True

            if w > 220:
                if last_instruction != "stop":
                    threading.Thread(target=speak, args=("Stop. You have reached the door. You are now good to go out!",)).start()
                    last_instruction = "stop"
            else:
                offset = x_center - FRAME_CENTER

                if abs(offset) < 50:
                    if last_instruction != "straight":
                        phrase = encouraging_phrases[current_phrase_index % len(encouraging_phrases)]
                        threading.Thread(target=speak, args=(phrase,)).start()
                        last_instruction = "straight"
                        current_phrase_index += 1
                elif offset < 0:
                    if last_instruction != "left":
                        threading.Thread(target=speak, args=("Turn slightly left.",)).start()
                        last_instruction = "left"
                else:
                    if last_instruction != "right":
                        threading.Thread(target=speak, args=("Turn slightly right.",)).start()
                        last_instruction = "right"
        else:
            door_visible_count = 0
            door_not_visible_count += 1

            # If door was visible before but now not, and count exceeds threshold, assume reached
            # Require door to have been visible for at least 30 frames, max width > 150, and not visible for 60 frames
            if (door_previously_visible and door_not_visible_count > 60 and previous_max_visible > 30
                and max_door_width > 150 and last_instruction != "reached" and last_instruction != "stop"):
                threading.Thread(target=speak, args=("Congratulations! You have successfully reached the door. You are now good to go out!",)).start()
                last_instruction = "reached"
                previous_max_visible = 0
                max_door_width = 0
                door_previously_visible = False  # Reset after announcing
            elif last_instruction != "looking" and door_not_visible_count <= 30:
                threading.Thread(target=speak, args=("Looking for door.",)).start()
                last_instruction = "looking"

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
