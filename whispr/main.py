"""Whispr — local dictation tool with global hotkey."""

import threading
from pynput import keyboard

from whispr.recorder import Recorder, SAMPLE_RATE
from whispr.transcriber import transcribe, load_model
from whispr.typer import type_text

recorder = Recorder()


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
    if key == keyboard.Key.f5:
        on_toggle()
    elif key in (keyboard.Key.esc, keyboard.Key.enter) and recorder.is_recording:
        on_toggle()


def main():
    print("=" * 50)
    print("  Whispr — Local Dictation Tool")
    print("=" * 50)
    print()
    print("Loading model on startup...")
    load_model()
    print()
    print("Hotkey: Fn+F5 (toggle recording)")
    print("Press Ctrl+C to quit.")
    print()
    print("Note: Grant Accessibility permissions in")
    print("  System Settings > Privacy & Security > Accessibility")
    print("  for your terminal app.")
    print()

    with keyboard.Listener(on_press=on_press) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\nBye!")


if __name__ == "__main__":
    main()
