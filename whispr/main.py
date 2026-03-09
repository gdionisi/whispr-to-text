"""Whispr — local dictation tool with global hotkey."""

import threading
from pynput import keyboard

from whispr.recorder import Recorder, SAMPLE_RATE
from whispr.transcriber import transcribe, load_model
from whispr.typer import type_text

# Hotkey: Option + W
HOTKEY = {keyboard.Key.alt, keyboard.KeyCode.from_char("w")}

recorder = Recorder()
current_keys: set = set()


def on_toggle():
    """Toggle recording on/off."""
    if recorder.is_recording:
        audio = recorder.stop()
        if len(audio) < SAMPLE_RATE * 0.5:
            print("Recording too short, skipping.")
            return

        def process():
            print("Transcribing...")
            text = transcribe(audio, sample_rate=SAMPLE_RATE)
            if text:
                print(f"Transcribed: {text}")
                type_text(text)
            else:
                print("No speech detected.")

        threading.Thread(target=process, daemon=True).start()
    else:
        recorder.start()


def on_press(key):
    current_keys.add(key)
    if HOTKEY.issubset(current_keys):
        on_toggle()


def on_release(key):
    current_keys.discard(key)


def main():
    print("=" * 50)
    print("  Whispr — Local Dictation Tool")
    print("=" * 50)
    print()
    print("Loading model on startup...")
    load_model()
    print()
    print("Hotkey: Option + W (toggle recording)")
    print("Press Ctrl+C to quit.")
    print()
    print("Note: Grant Accessibility permissions in")
    print("  System Settings > Privacy & Security > Accessibility")
    print("  for your terminal app.")
    print()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\nBye!")


if __name__ == "__main__":
    main()
