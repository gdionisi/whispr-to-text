"""Whispr — local dictation tool with menu bar icon and global hotkey."""

import threading
import rumps
from pynput import keyboard

from whispr.recorder import Recorder, SAMPLE_RATE
from whispr.transcriber import transcribe, load_model
from whispr.typer import type_text

ICON_IDLE = "🎤"
ICON_RECORDING = "🔴"
ICON_PROCESSING = "⏳"


class WhisprApp(rumps.App):
    def __init__(self):
        super().__init__("Whispr", title=ICON_IDLE)
        self.recorder = Recorder()
        self.menu = [
            rumps.MenuItem("Toggle Recording (Fn+F5)", callback=self._on_menu_toggle),
            None,  # separator
            rumps.MenuItem("Status: Idle"),
        ]
        self._status_item = self.menu["Status: Idle"]

    def start(self):
        print("Loading Whisper model...")
        load_model()
        print("Model loaded. Starting menu bar app...")

        # Start global hotkey listener in background
        listener = keyboard.Listener(on_press=self._on_press)
        listener.daemon = True
        listener.start()

        self.run()

    def _on_press(self, key):
        if key == keyboard.Key.f5:
            self._toggle()
        elif key in (keyboard.Key.esc, keyboard.Key.enter) and self.recorder.is_recording:
            self._toggle()

    def _on_menu_toggle(self, _):
        self._toggle()

    def _toggle(self):
        if self.recorder.is_recording:
            audio = self.recorder.stop()
            self.title = ICON_PROCESSING
            self._status_item.title = "Status: Transcribing..."

            if len(audio) < SAMPLE_RATE * 0.5:
                print("Recording too short, skipping.")
                self.title = ICON_IDLE
                self._status_item.title = "Status: Idle"
                return

            def process():
                print("Transcribing...")
                text = transcribe(audio, sample_rate=SAMPLE_RATE)
                if text:
                    print(f"Transcribed: {text}")
                    type_text(text)
                else:
                    print("No speech detected.")
                self.title = ICON_IDLE
                self._status_item.title = "Status: Idle"

            threading.Thread(target=process, daemon=True).start()
        else:
            self.recorder.start()
            self.title = ICON_RECORDING
            self._status_item.title = "Status: Recording..."


def main():
    app = WhisprApp()
    app.start()


if __name__ == "__main__":
    main()
