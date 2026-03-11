"""Configuration management for Whispr."""

import json
import os

from pynput import keyboard

CONFIG_DIR = os.path.expanduser("~/Library/Application Support/Whispr")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "toggle_key": "f5",
    "stop_keys": ["escape", "return"],
    "language": "en",
    "welcome_shown": False,
}

# Whisper supported languages: code -> display name
LANGUAGES = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "uk": "Ukrainian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "cs": "Czech",
    "ro": "Romanian",
    "el": "Greek",
    "he": "Hebrew",
    "hu": "Hungarian",
    "ca": "Catalan",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
}

# Modifier names recognized in hotkey combos
MODIFIER_NAMES = ("cmd", "ctrl", "alt", "shift")

# pynput modifier keys -> modifier name (left and right variants)
_PYNPUT_MODIFIERS = {
    keyboard.Key.cmd: "cmd",
    keyboard.Key.cmd_r: "cmd",
    keyboard.Key.ctrl: "ctrl",
    keyboard.Key.ctrl_r: "ctrl",
    keyboard.Key.alt: "alt",
    keyboard.Key.alt_r: "alt",
    keyboard.Key.shift: "shift",
    keyboard.Key.shift_r: "shift",
}

# Quartz CGEvent modifier flags (plain ints to avoid importing Quartz here)
QUARTZ_MOD_FLAGS = {
    "cmd": 0x100000,    # kCGEventFlagMaskCommand
    "ctrl": 0x40000,    # kCGEventFlagMaskControl
    "alt": 0x80000,     # kCGEventFlagMaskAlternate
    "shift": 0x20000,   # kCGEventFlagMaskShift
}

# Special key mapping: config_name -> (display_name, pynput_key, quartz_keycode)
_KEY_INFO = {
    "escape": ("Escape", keyboard.Key.esc, 53),
    "return": ("Return", keyboard.Key.enter, 36),
    "tab": ("Tab", keyboard.Key.tab, 48),
    "space": ("Space", keyboard.Key.space, 49),
    "delete": ("Delete", keyboard.Key.delete, 51),
    "f1": ("F1", keyboard.Key.f1, 122),
    "f2": ("F2", keyboard.Key.f2, 120),
    "f3": ("F3", keyboard.Key.f3, 99),
    "f4": ("F4", keyboard.Key.f4, 118),
    "f5": ("F5", keyboard.Key.f5, 96),
    "f6": ("F6", keyboard.Key.f6, 97),
    "f7": ("F7", keyboard.Key.f7, 98),
    "f8": ("F8", keyboard.Key.f8, 100),
    "f9": ("F9", keyboard.Key.f9, 101),
    "f10": ("F10", keyboard.Key.f10, 109),
    "f11": ("F11", keyboard.Key.f11, 103),
    "f12": ("F12", keyboard.Key.f12, 111),
}

# macOS virtual keycodes for character keys
_CHAR_KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7,
    "c": 8, "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15,
    "y": 16, "t": 17, "o": 31, "u": 32, "i": 34, "p": 35, "l": 37,
    "j": 38, "k": 40, "n": 45, "m": 46,
    "1": 18, "2": 19, "3": 20, "4": 21, "5": 23, "6": 22, "7": 26,
    "8": 28, "9": 25, "0": 29,
    "-": 27, "=": 24, "[": 33, "]": 30, ";": 41, "'": 39, ",": 43,
    ".": 47, "/": 44, "\\": 42, "`": 50,
}

# Reverse lookup: pynput special key -> key name
_PYNPUT_TO_NAME = {info[1]: name for name, info in _KEY_INFO.items()}

# Display names for modifiers
_MOD_DISPLAY = {"cmd": "Cmd", "ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}


# ── Hotkey parsing ────────────────────────────────────────────────────

def parse_hotkey(hotkey_str: str) -> tuple[frozenset[str], str]:
    """Parse 'cmd+shift+r' -> (frozenset({'cmd', 'shift'}), 'r')."""
    parts = hotkey_str.split("+")
    mods = frozenset(p for p in parts[:-1] if p in MODIFIER_NAMES)
    key = parts[-1]
    return mods, key


def format_hotkey(mods: frozenset[str], key: str) -> str:
    """Format (frozenset({'cmd', 'shift'}), 'r') -> 'cmd+shift+r'."""
    parts = sorted(mods) + [key]
    return "+".join(parts)


def _is_valid_key(name: str) -> bool:
    """Check if a base key name is valid (special or character key)."""
    return name in _KEY_INFO or name in _CHAR_KEYCODES


def _is_valid_hotkey(hotkey_str: str) -> bool:
    """Check if a full hotkey string is valid."""
    mods, key = parse_hotkey(hotkey_str)
    return _is_valid_key(key) and all(m in MODIFIER_NAMES for m in mods)


# ── Config I/O ────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load config from disk, falling back to defaults for missing/invalid keys."""
    config = dict(DEFAULT_CONFIG)
    config["stop_keys"] = list(DEFAULT_CONFIG["stop_keys"])
    try:
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        if _is_valid_hotkey(saved.get("toggle_key", "")):
            config["toggle_key"] = saved["toggle_key"]
        stop = saved.get("stop_keys")
        if isinstance(stop, list) and all(_is_valid_hotkey(k) for k in stop):
            config["stop_keys"] = stop
        lang = saved.get("language", "")
        if lang in LANGUAGES:
            config["language"] = lang
        if saved.get("welcome_shown"):
            config["welcome_shown"] = True
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return config


def save_config(config: dict):
    """Save config to disk."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# ── Key info helpers ──────────────────────────────────────────────────

def display_name(hotkey_str: str) -> str:
    """Get human-readable display name for a hotkey string like 'cmd+shift+r'."""
    mods, key = parse_hotkey(hotkey_str)
    # Format key part
    info = _KEY_INFO.get(key)
    if info:
        key_display = info[0]
    elif key in _CHAR_KEYCODES:
        key_display = key.upper()
    else:
        key_display = key
    # Format modifiers
    if mods:
        mod_parts = [_MOD_DISPLAY.get(m, m) for m in sorted(mods)]
        return "+".join(mod_parts + [key_display])
    return key_display


def quartz_keycode(hotkey_str: str) -> int | None:
    """Get Quartz keycode for the base key of a hotkey string."""
    _, key = parse_hotkey(hotkey_str)
    info = _KEY_INFO.get(key)
    if info:
        return info[2]
    return _CHAR_KEYCODES.get(key)


def quartz_mod_mask(hotkey_str: str) -> int:
    """Get combined Quartz modifier flag mask for a hotkey string."""
    mods, _ = parse_hotkey(hotkey_str)
    mask = 0
    for m in mods:
        mask |= QUARTZ_MOD_FLAGS.get(m, 0)
    return mask


def pynput_key(hotkey_str: str):
    """Get pynput Key/KeyCode for the base key of a hotkey string."""
    _, key = parse_hotkey(hotkey_str)
    info = _KEY_INFO.get(key)
    if info:
        return info[1]
    if key in _CHAR_KEYCODES:
        return keyboard.KeyCode.from_char(key)
    return None


def pynput_mods(hotkey_str: str) -> frozenset[str]:
    """Get the modifier names for a hotkey string."""
    mods, _ = parse_hotkey(hotkey_str)
    return mods


def is_modifier(key) -> bool:
    """Check if a pynput key is a modifier."""
    return key in _PYNPUT_MODIFIERS


def modifier_name(key) -> str | None:
    """Get modifier name from a pynput modifier key."""
    return _PYNPUT_MODIFIERS.get(key)


def key_name_from_pynput(key) -> str | None:
    """Get config key name from a pynput non-modifier key, or None if unsupported."""
    name = _PYNPUT_TO_NAME.get(key)
    if name:
        return name
    if isinstance(key, keyboard.KeyCode) and key.char:
        char = key.char.lower()
        if char in _CHAR_KEYCODES:
            return char
    return None
