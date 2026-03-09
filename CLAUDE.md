# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Whispr is a macOS-only local speech-to-text dictation tool. It runs as a menu bar app (no Dock icon), listens for a configurable global hotkey (default: F5), records audio from the microphone, transcribes it locally using Whisper via whisper.cpp, and pastes the result into the focused application. Hotkeys (including modifier combos like Cmd+Shift+R) are configurable via the menu bar interface and persist in `~/Library/Application Support/Whispr/config.json`.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Run
whispr                    # via entry point
python -m whispr.main     # directly

# Build macOS .app bundle
pip install pyinstaller
pyinstaller whispr.spec   # outputs to dist/Whispr.app
```

## Architecture

The app has five modules under `whispr/`:

- **main.py** — Entry point. `WhisprApp` subclasses `rumps.App` for the menu bar UI. Registers a global hotkey listener (`pynput`) with press/release tracking for modifier combos. Toggle and stop keys are loaded from config. Menu bar includes key binding preferences with a capture mode (click to set, then press desired key combo). Whisper model loads in a background thread on startup (shows "Loading..." in menu bar). Quartz event tap suppresses stop keys during recording.
- **config.py** — Configuration management. Loads/saves hotkey bindings from `~/Library/Application Support/Whispr/config.json`. Maps between config key names, display names, pynput keys, and Quartz keycodes. Supports single keys and modifier combos (e.g., `cmd+shift+r`). Validates config on load with fallback to defaults (F5 toggle, Escape/Return stop).
- **recorder.py** — `Recorder` class wraps `sounddevice.InputStream` to capture 16kHz mono float32 audio. Thread-safe start/stop with lock.
- **transcriber.py** — Loads a whisper.cpp model via `pywhispercpp` (singleton pattern). `transcribe()` takes a numpy audio array and returns text. Model downloads automatically on first use (~466MB for "small").
- **typer.py** — Outputs text by copying to clipboard (`pbcopy`), simulating Cmd+V via AppleScript (`osascript`), then restoring the previous clipboard contents.

## Key Details

- **macOS only**: Uses `rumps` (menu bar), `AppKit` (hide from Dock), `pbcopy`/`pbpaste`, and `osascript`.
- **Accessibility permission** required for `pynput` (global hotkey) and AppleScript keystroke simulation.
- **Microphone permission** required for `sounddevice`.
- Whisper model files are stored in the pywhispercpp cache directory (not in the repo). Model auto-downloads on first launch (~466MB for "small").
- `LSUIElement: True` in the spec file makes the app run without a Dock icon.
- **Icon assets** in repo root: `icon.png` (source), `icon.icns` (app bundle icon for Finder/Spotlight), `icon_menubar.png` (22px menu bar icon). Asset paths use `sys._MEIPASS` fallback for PyInstaller bundles.
