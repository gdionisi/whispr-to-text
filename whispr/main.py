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
from whispr.config import (
    load_config, save_config, display_name,
    pynput_key, pynput_mods, quartz_keycode, quartz_mod_mask,
    key_name_from_pynput, is_modifier, modifier_name,
    format_hotkey, parse_hotkey, QUARTZ_MOD_FLAGS, LANGUAGES,
)

_BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))
_icon = os.path.join(_BASE, "icon_menubar.png")
_ICON_PATH = _icon if os.path.exists(_icon) else None
_app_icon = os.path.join(_BASE, "icon.png")
_APP_ICON_PATH = _app_icon if os.path.exists(_app_icon) else None


class WhisprApp(rumps.App):
    def __init__(self):
        super().__init__("Whispr", icon=_ICON_PATH, template=True)
        self.recorder = Recorder()
        self._tap = None
        self._tap_source = None
        self._capture_target = None  # "toggle" or "stop" when capturing a key
        self._held_mods: set[str] = set()  # currently held modifier names

        # Load user config
        self._config = load_config()

        # Build language submenu
        self._lang_menu = rumps.MenuItem("Language")
        self._lang_items = {}
        for code, name in LANGUAGES.items():
            item = rumps.MenuItem(name, callback=self._on_language_select)
            item._lang_code = code
            if code == self._config["language"]:
                item.state = 1
            self._lang_items[code] = item
            self._lang_menu.add(item)

        self.menu = [
            rumps.MenuItem("Toggle Recording", callback=self._on_menu_toggle),
            None,  # separator
            rumps.MenuItem("Status: Idle"),
            None,  # separator
            self._lang_menu,
            None,  # separator
            rumps.MenuItem("Set Toggle Key", callback=self._on_set_toggle_key),
            rumps.MenuItem("Set Stop Key", callback=self._on_set_stop_key),
            rumps.MenuItem("Reset Key Bindings", callback=self._on_reset_keys),
            None,  # separator
            rumps.MenuItem("Help", callback=self._on_help),
        ]
        self._status_item = self.menu["Status: Idle"]
        self._update_menu_labels()

    def _update_menu_labels(self):
        """Update menu item titles to reflect current key config."""
        toggle = display_name(self._config["toggle_key"])
        self.menu["Toggle Recording"].title = f"Toggle Recording ({toggle})"

        stop_names = ", ".join(
            display_name(k) for k in self._config["stop_keys"]
        )
        self.menu["Set Toggle Key"].title = f"Toggle Key: {toggle} (click to change)"
        self.menu["Set Stop Key"].title = (
            f"Stop Key: {stop_names or 'None'} (click to change)"
        )

    def start(self):
        # Global hotkey listener (non-suppressing) with press and release
        listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        listener.daemon = True
        listener.start()

        # Show welcome dialog on first launch (before model download)
        if not self._config.get("welcome_shown"):
            if not self._show_welcome():
                # User cancelled — quit before downloading anything
                return

        # Load model in background so the menu bar appears immediately
        self._model_ready = False
        self.title = "Loading..."
        threading.Thread(target=self._load_model, daemon=True).start()

        self.run()

    def _show_welcome(self) -> bool:
        """Show a one-time welcome dialog. Returns True to proceed, False to quit."""
        accepted = self._show_help_dialog(first_launch=True)
        if accepted:
            self._config["welcome_shown"] = True
            save_config(self._config)
        return accepted

    def _on_help(self, _):
        """Show the help/instructions dialog."""
        self._show_help_dialog(first_launch=False)

    def _show_help_dialog(self, first_launch: bool) -> bool:
        """Show the instructions dialog. Returns True if user accepted."""
        toggle = display_name(self._config["toggle_key"])
        stop_names = ", ".join(
            display_name(k) for k in self._config["stop_keys"]
        )
        sections = []
        sections.append(
            "Whispr is a local speech-to-text dictation tool. "
            "Everything runs on your machine — no internet needed."
        )
        if first_launch:
            sections.append(
                "MODEL DOWNLOAD\n"
                "Whispr needs a speech recognition model (~466 MB) to work. "
                "It will be downloaded automatically when you click "
                "\"Continue\". This only happens once — subsequent launches "
                "are instant."
            )
        sections.append(
            "PERMISSIONS REQUIRED\n"
            "Go to System Settings → Privacy & Security and grant:\n"
            "• Accessibility — for global hotkeys and pasting text\n"
            "• Microphone — for recording audio\n"
            "• Input monitoring — to detect when hotkeys are pressed"
        )
        sections.append(
            f"HOW TO USE\n"
            f"• Press {toggle} to start recording (icon turns red)\n"
            f"• Speak into your microphone\n"
            f"• Press {stop_names} to stop (text is pasted automatically)"
        )
        sections.append(
            "CUSTOMISE HOTKEYS\n"
            "Click the menu bar icon to change toggle/stop keys. "
            "Modifier combos (e.g., Cmd+Shift+R) are supported."
        )
        if first_launch:
            title = "Welcome to Whispr"
            ok_text = "Continue"
            cancel = "Quit"
        else:
            title = "Whispr — Help"
            ok_text = "OK"
            cancel = None
        response = rumps.alert(
            title=title,
            message="\n\n".join(sections),
            ok=ok_text,
            cancel=cancel,
            icon_path=_APP_ICON_PATH,
        )
        # rumps.alert returns 1 for OK, 0 for Cancel
        return response == 1

    def _load_model(self):
        print("Loading Whisper model...")
        load_model()
        print("Model loaded.")
        self._model_ready = True
        self.title = None

    # ── Key capture mode ──────────────────────────────────────────────

    def _on_set_toggle_key(self, _):
        """Enter capture mode for the toggle key."""
        if self.recorder.is_recording:
            return
        self._capture_target = "toggle"
        self.title = "⌨️"
        self._status_item.title = "Press a key combo for Toggle..."

    def _on_set_stop_key(self, _):
        """Enter capture mode for the stop key."""
        if self.recorder.is_recording:
            return
        self._capture_target = "stop"
        self.title = "⌨️"
        self._status_item.title = "Press a key combo for Stop..."

    def _on_language_select(self, sender):
        """Handle language selection from submenu."""
        code = sender._lang_code
        self._config["language"] = code
        save_config(self._config)
        # Update checkmarks
        for c, item in self._lang_items.items():
            item.state = 1 if c == code else 0

    def _on_reset_keys(self, _):
        """Reset key bindings to defaults."""
        from whispr.config import DEFAULT_CONFIG
        self._config["toggle_key"] = DEFAULT_CONFIG["toggle_key"]
        self._config["stop_keys"] = list(DEFAULT_CONFIG["stop_keys"])
        save_config(self._config)
        self._update_menu_labels()
        self._status_item.title = "Status: Keys reset to defaults"

    def _handle_capture(self, key):
        """Handle a keypress during capture mode. Returns True if handled."""
        if self._capture_target is None:
            return False

        # Ignore modifier-only presses — wait for the actual key
        if is_modifier(key):
            return True

        name = key_name_from_pynput(key)
        if name is None:
            return True

        # Build hotkey string from held modifiers + key
        hotkey = format_hotkey(frozenset(self._held_mods), name)

        if self._capture_target == "toggle":
            self._config["toggle_key"] = hotkey
        elif self._capture_target == "stop":
            self._config["stop_keys"] = [hotkey]

        save_config(self._config)
        self._capture_target = None
        self.title = None
        self._update_menu_labels()
        self._status_item.title = "Status: Idle"
        return True

    # ── Hotkey handling ───────────────────────────────────────────────

    def _on_press(self, key):
        # Track modifier state
        mod = modifier_name(key)
        if mod:
            self._held_mods.add(mod)

        # Capture mode takes priority
        if self._handle_capture(key):
            return

        # Check for toggle key (match base key + modifiers)
        toggle_str = self._config["toggle_key"]
        toggle_key = pynput_key(toggle_str)
        toggle_mods = pynput_mods(toggle_str)
        if key == toggle_key and self._held_mods == set(toggle_mods):
            self._toggle()

    def _on_release(self, key):
        # Untrack modifier state
        mod = modifier_name(key)
        if mod:
            self._held_mods.discard(mod)

    def _suppress_tap_callback(self, proxy, event_type, event, refcon):
        """Quartz event tap: suppress stop key combos and trigger stop."""
        # macOS disables taps that are too slow to respond — re-enable
        if event_type == Quartz.kCGEventTapDisabledByTimeout:
            print("Event tap disabled by timeout, re-enabling...")
            Quartz.CGEventTapEnable(self._tap, True)
            return event

        kc = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode
        )
        flags = Quartz.CGEventGetFlags(event)

        for stop_hotkey in self._config["stop_keys"]:
            expected_kc = quartz_keycode(stop_hotkey)
            expected_mod_mask = quartz_mod_mask(stop_hotkey)

            if kc != expected_kc:
                continue

            # Check that all required modifiers are held
            # (use device-independent flags only)
            if expected_mod_mask:
                if (flags & expected_mod_mask) != expected_mod_mask:
                    continue

            # For combos without modifiers, make sure no modifiers are held
            if not expected_mod_mask:
                held_mods = 0
                for flag in QUARTZ_MOD_FLAGS.values():
                    held_mods |= flags & flag
                if held_mods:
                    continue

            threading.Thread(target=self._toggle, daemon=True).start()
            return None  # suppress this key

        return event

    def _start_suppress_tap(self):
        """Install a Quartz event tap to suppress stop keys."""
        mask = Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
        # Also capture flagsChanged events for modifier-based combos
        mask |= Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            mask,
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
        if not self._model_ready:
            return
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
                try:
                    print("Transcribing...")
                    text = transcribe(audio, sample_rate=SAMPLE_RATE, language=self._config["language"])
                    if text:
                        print(f"Transcribed: {text}")
                        type_text(text)
                    else:
                        print("No speech detected.")
                except Exception as e:
                    print(f"Error during transcription: {e}")
                    import traceback
                    traceback.print_exc()
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
