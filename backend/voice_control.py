import speech_recognition as sr
import time

STATUS_FILE = "nav_status.txt"

def set_status(state):
    with open(STATUS_FILE, "w") as f:
        f.write(state)

set_status("STOP")  # initially stop navigation

r = sr.Recognizer()

while True:
    try:
        with sr.Microphone() as source:
            print("\n🎤 Say: 'guide me to the door' or 'stop navigation'")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout=5, phrase_time_limit=4)

        command = r.recognize_google(audio).lower()
        print("Heard:", command)

        if "guide me to the door" in command:
            print("✅ Navigation Activated")
            set_status("START")

        elif "stop navigation" in command:
            print("⛔ Navigation Paused")
            set_status("STOP")

    except:
        pass

    time.sleep(1)
