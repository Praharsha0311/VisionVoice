import pyautogui
import pytesseract
from PIL import ImageGrab
import requests
import time
from pywinauto import Desktop

# Optional: specify your Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

TTS_URL = "http://127.0.0.1:5000/speak"
SPEAK_INTERVAL = 1.5  # seconds between speeches
REGION_SIZE = 180     # area captured around mouse for OCR

last_text = ""
last_time = 0

# 👇 Define custom context messages
CONTEXT_MESSAGES = {
    "new tab": "You are on the New Tab button",
    "chrome": "You are in Google Chrome",
    "recycle bin": "You are on the Recycle Bin icon",
    "taskbar": "You are on the Windows Taskbar",
    "start": "You are on the Start menu",
    "vscode": "You are inside Visual Studio Code",
    "desktop": "You are on the Desktop",
    "file explorer": "You are in File Explorer",
    "search": "You are on the Search bar",
    "edge": "You are using Microsoft Edge browser"
}

def get_accessible_text(x, y):
    """Try to get accessible name of element using Windows UI Automation."""
    try:
        ctrl = Desktop(backend="uia").from_point(x, y)
        name = ctrl.window_text()
        if name:
            return name.strip()
    except Exception:
        pass
    return None

def get_ocr_text(x, y):
    """Fallback: OCR capture of small region under cursor."""
    bbox = (x - REGION_SIZE // 2, y - 25, x + REGION_SIZE // 2, y + 25)
    img = ImageGrab.grab(bbox)
    text = pytesseract.image_to_string(img, lang='eng').strip()
    return text

def detect_contextual_message(text):
    """Return a friendly contextual message if known."""
    t = text.lower()
    for keyword, message in CONTEXT_MESSAGES.items():
        if keyword in t:
            return message
    return None  # fallback to normal text

def speak_text(text):
    """Send text to Flask server (Sarvam TTS)."""
    try:
        requests.post(TTS_URL, json={"text": text}, timeout=5)
    except Exception as e:
        print("TTS send error:", e)

def main():
    global last_text, last_time
    print("🖱️ Hover Speech Assistant started... Move your mouse anywhere!")

    while True:
        try:
            x, y = pyautogui.position()

            # First try accessible name (UIA)
            text = get_accessible_text(x, y)

            # If no UI name found, try OCR fallback
            if not text:
                text = get_ocr_text(x, y)

            if text and text != last_text:
                now = time.time()
                if now - last_time > SPEAK_INTERVAL:
                    # Detect if text matches any known context
                    custom_message = detect_contextual_message(text)
                    message_to_speak = custom_message if custom_message else text

                    print(f"🗣️ Speaking: {message_to_speak}")
                    speak_text(message_to_speak)

                    last_text = text
                    last_time = now

            time.sleep(0.8)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
