"""Whispr — local dictation tool with menu bar icon and global hotkey."""

import os
import sys
import threading
import rumps
import Quartz
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
from pynput import keyboard

from whispr.recorder import Recorder, SAMPLE_RATE
from whispr.transcriber import transcribe, load_model
from whispr.typer import type_text

_BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))
_ICON_PATH = os.path.join(_BASE, "icon_menubar.png")

# macOS keycodes for Escape and Return
_KC_ESCAPE = 53
_KC_RETURN = 36


class WhisprApp(rumps.App):
    def __init__(self):
        super().__init__("Whispr", icon=_ICON_PATH, template=True)
        self.recorder = Recorder()
        self._tap = None
        self._tap_source = None
        self.menu = [
            rumps.MenuItem("Toggle Recording (Fn+F5)", callback=self._on_menu_toggle),
            None,  # separator
            rumps.MenuItem("Status: Idle"),
            None,  # separator
            rumps.MenuItem("Quit Whispr", callback=self._on_quit),
        ]
        self._status_item = self.menu["Status: Idle"]

    def start(self):
        print("Loading Whisper model...")
        load_model()
        print("Model loaded. Starting menu bar app...")

        # Global hotkey listener (non-suppressing)
        listener = keyboard.Listener(on_press=self._on_press)
        listener.daemon = True
        listener.start()

        self.run()

    def _on_press(self, key):
        if key == keyboard.Key.f5:
            self._toggle()

    def _suppress_tap_callback(self, proxy, event_type, event, refcon):
        """Quartz event tap: suppress Esc/Enter and trigger stop recording."""
        keycode = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode
        )
        if keycode in (_KC_ESCAPE, _KC_RETURN):
            threading.Thread(target=self._toggle, daemon=True).start()
            return None  # suppress this key
        return event

    def _start_suppress_tap(self):
        """Install a Quartz event tap to suppress Esc/Enter."""
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown),
            self._suppress_tap_callback,
            None,
        )
        if self._tap:
            self._tap_source = Quartz.CFMachPortCreateRunLoopSource(
                None, self._tap, 0
            )
            Quartz.CFRunLoopAddSource(
                Quartz.CFRunLoopGetMain(),
                self._tap_source,
                Quartz.kCFRunLoopCommonModes,
            )

    def _stop_suppress_tap(self):
        """Fully disable and remove the Quartz event tap."""
        if self._tap:
            Quartz.CGEventTapEnable(self._tap, False)
        if self._tap_source:
            Quartz.CFRunLoopRemoveSource(
                Quartz.CFRunLoopGetMain(),
                self._tap_source,
                Quartz.kCFRunLoopCommonModes,
            )
            self._tap_source = None
        if self._tap:
            Quartz.CFMachPortInvalidate(self._tap)
            self._tap = None

    def _on_menu_toggle(self, _):
        self._toggle()

    def _on_quit(self, _):
        rumps.quit_application()

    def _toggle(self):
        if self.recorder.is_recording:
            self._stop_suppress_tap()
            audio = self.recorder.stop()
            self.title = "⏳"
            self._status_item.title = "Status: Transcribing..."

            if len(audio) < SAMPLE_RATE * 0.5:
                print("Recording too short, skipping.")
                self.title = None
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
                self.title = None
                self._status_item.title = "Status: Idle"

            threading.Thread(target=process, daemon=True).start()
        else:
            self.recorder.start()
            self._start_suppress_tap()
            self.title = "🔴"
            self._status_item.title = "Status: Recording..."


def main():
    # Hide Python from Dock — run as menu bar-only app
    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )
    app = WhisprApp()
    app.start()


if __name__ == "__main__":
    main()
