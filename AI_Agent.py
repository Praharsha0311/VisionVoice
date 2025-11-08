import datetime
import json
import os
import os.path
import queue
import subprocess
import threading
import time
import webbrowser
import pyautogui
import pyttsx3
import sounddevice as sd
import zipfile
import wave
import io
from groq import Groq
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# List of available commands
commands = [
    "open google",
    "open chrome",
    "open music",
    "the time",
    "play",
    "send email",
    "open notepad",
    "close notepad",
    "save notepad",
    "save file",
    "save",
    "save the file",
    "write",
    "type",
    "open calculator",
    "calculate",
    "open file explorer",
    "search",
    "take screenshot",
    "shutdown",
    "exit",
    "stop"
]

# Function to find the best matching command
def find_best_match(text, commands):
    best_match = None
    best_ratio = 0.0

    # Clean the text
    text = text.lower().strip()

    for command in commands:
        command_lower = command.lower()

        # Check for exact match first
        if text == command_lower:
            return command, 1.0

        # Check if command is contained in text
        if command_lower in text:
            return command, 0.9

        # Check individual words - more flexible matching
        command_words = command_lower.split()
        text_words = text.split()

        # If all command words are in text (in any order)
        if all(word in text_words for word in command_words):
            return command, 0.8

        # Check for partial matches (at least 2 words match for multi-word commands)
        matching_words = sum(1 for word in command_words if word in text_words)
        if len(command_words) > 1 and matching_words >= 2:
            confidence = 0.7 + (matching_words / len(command_words)) * 0.2
            if confidence > best_ratio:
                best_ratio = confidence
                best_match = command

        # Similarity ratio as fallback
        ratio = SequenceMatcher(None, text, command_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = command

    return best_match, best_ratio

# Queue to hold audio data
q = queue.Queue()

# Callback function to capture audio input
def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Function to listen for voice input and transcribe using Groq
def listen():
    # Clear the queue before starting
    while not q.empty():
        q.get()

    audio_data = []
    silence_threshold = 5  # Stop listening after 5 seconds of silence
    last_audio_time = time.time()

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("Listening... Speak now.")
        start_time = time.time()

        while time.time() - start_time < 10:  # Max 10 seconds total
            try:
                data = q.get(timeout=0.5)  # Shorter timeout for better responsiveness
                audio_data.append(data)
                last_audio_time = time.time()  # Reset silence timer when audio is detected
            except queue.Empty:
                # Check if we've had silence for too long
                if time.time() - last_audio_time > silence_threshold:
                    break
                continue

        if not audio_data:
            print("No speech detected.")
            return ""

        # Convert raw audio data to WAV format
        audio_bytes = b''.join(audio_data)
        # Convert int16 bytes to numpy array for WAV creation
        import numpy as np
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(audio_array.tobytes())

        wav_buffer.seek(0)
        wav_data = wav_buffer.getvalue()

        # Transcribe using Groq with faster model
        try:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_data, "audio/wav"),
                model="whisper-large-v3",  # Keep high accuracy but optimize processing
                response_format="json",
                language="en",
                temperature=0  # More deterministic for speed
            )
            text = transcription.text.strip()
            if text:
                print("You said:", text)
                return text.lower()
            else:
                print("No speech detected.")
                return ""
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""

# Function to convert text to speech
def say(text):
    def speak():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    # Run speech in a separate thread to avoid blocking
    speech_thread = threading.Thread(target=speak)
    speech_thread.start()
    speech_thread.join()  # Wait for speech to finish

# Function to get weather updates
def get_weather(city):
    api_key = "e9ac9860f40e984df6654a801c9cbf35"  # Replace with your OpenWeather API key
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    weather_data = response.json()

    if weather_data["cod"] != "404":
        main = weather_data["main"]
        wind = weather_data["wind"]
        weather_desc = weather_data["weather"][0]["description"]

        temperature = main["temp"]
        humidity = main["humidity"]
        wind_speed = wind["speed"]

        weather_report = (f"Temperature: {temperature}°C\n"
                          f"Humidity: {humidity}%\n"
                          f"Wind Speed: {wind_speed} m/s\n"
                          f"Weather Description: {weather_desc}")
    else:
        weather_report = "City Not Found"
    return weather_report

# Function to send an email
def send_email(recipient, subject, body):
    sender_email = "your_email@gmail.com"
    sender_password = "your_password"  # Use app password for Gmail if 2FA is enabled

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient, text)
        server.quit()
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Function to open Notepad
def open_notepad():
    try:
        subprocess.Popen(['notepad.exe'])
        return "Notepad opened."
    except Exception as e:
        return f"Failed to open Notepad: {str(e)}"

# Function to close Notepad
def close_notepad():
    try:
        # Find and close notepad process
        subprocess.run(['taskkill', '/f', '/im', 'notepad.exe'], capture_output=True)
        return "Notepad closed."
    except Exception as e:
        return f"Failed to close Notepad: {str(e)}"

# Function to save Notepad file
def save_notepad():
    try:
        # Simulate Ctrl+S to save
        pyautogui.hotkey('ctrl', 's')
        return "Notepad file saved."
    except Exception as e:
        return f"Failed to save Notepad: {str(e)}"

# Function to type text (assumes active window is where to type)
def type_text(text):
    try:
        pyautogui.write(text, interval=0.05)
        return f"Typed: {text}"
    except Exception as e:
        return f"Failed to type text: {str(e)}"

# Function to open Calculator
def open_calculator():
    try:
        subprocess.Popen(['calc.exe'])
        return "Calculator opened."
    except Exception as e:
        return f"Failed to open Calculator: {str(e)}"

# Function to open File Explorer
def open_file_explorer():
    try:
        subprocess.Popen(['explorer.exe'])
        return "File Explorer opened."
    except Exception as e:
        return f"Failed to open File Explorer: {str(e)}"

# Function to search in browser
def search_browser(query):
    try:
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Searched for: {query}"
    except Exception as e:
        return f"Failed to search: {str(e)}"

# Function to take screenshot
def take_screenshot():
    try:
        import os
        screenshot = pyautogui.screenshot()
        filepath = os.path.join(os.getcwd(), "screenshot.png")
        screenshot.save(filepath)
        print(f"Screenshot saved to: {filepath}")
        return f"Screenshot taken and saved as {filepath}"
    except Exception as e:
        print(f"Screenshot error: {str(e)}")
        return f"Failed to take screenshot: {str(e)}"

# Function to shutdown computer
def shutdown_computer():
    try:
        os.system("shutdown /s /t 1")
        return "Shutting down the computer."
    except Exception as e:
        return f"Failed to shutdown: {str(e)}"

if __name__ == "__main__":
    path = r"C:\Users\lenovo thinkbook\Downloads\chasing-horizons-228832.mp3"

    while True:
        text = listen()
        if not text:
            continue  # Skip if no speech detected

        # Find the best matching command
        best_command, confidence = find_best_match(text, commands)

        if best_command and confidence > 0.6:  # Threshold for command recognition
            print(f"Recognized command: {best_command} (confidence: {confidence:.2f})")

            if best_command == "open google":
                webbrowser.open("https://google.com")
                say("Opening Google")
            elif best_command == "open chrome":
                try:
                    subprocess.Popen(['chrome.exe'])
                    say("Opening Chrome")
                except Exception as e:
                    say("Chrome not found. Opening Google instead.")
                    webbrowser.open("https://google.com")
            elif best_command == "open music":
                os.startfile(path)
                say("Playing music")
            elif best_command == "the time":
                curhr = datetime.datetime.now().strftime("%H")
                curmin = datetime.datetime.now().strftime("%M")
                say(f"Sir, the time is {curhr} hours and {curmin} minutes")
            elif best_command == "play":
                say("Which city?")
                city = listen()
                weather = get_weather(city)
                say(f"The weather in {city} is as follows:\n{weather}")
            elif best_command == "send email":
                say("Please provide the recipient email address.")
                recipient = listen()
                say("What is the subject?")
                subject = listen()
                say("What would you like to say?")
                body = listen()
                email_status = send_email(recipient, subject, body)
                say(email_status)
            elif best_command == "open notepad":
                status = open_notepad()
                say(status)
            elif best_command == "close notepad":
                status = close_notepad()
                say(status)
            elif best_command == "save notepad":
                status = save_notepad()
                say(status)
            elif best_command in ["save file", "save", "save the file"]:
                status = save_notepad()
                say(status)
            elif best_command == "write":
                say("What would you like to write?")
                text_to_write = listen()
                status = type_text(text_to_write)
                say(status)
            elif best_command == "type":
                say("What would you like to type?")
                text_to_write = listen()
                status = type_text(text_to_write)
                say(status)
            elif best_command in ["open calculator", "calculate"]:
                status = open_calculator()
                say(status)
            elif best_command == "open file explorer":
                status = open_file_explorer()
                say(status)
            elif best_command == "search":
                say("What would you like to search?")
                query = listen()
                status = search_browser(query)
                say(status)
            elif best_command == "take screenshot":
                status = take_screenshot()
                say(status)
            elif best_command == "shutdown":
                status = shutdown_computer()
                say(status)
            elif best_command in ["exit", "stop"]:
                say("Goodbye!")
                break
        else:
            print(f"Unrecognized command: {text}")
            say("Sorry, I didn't understand that command.")
