# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Whispr is a macOS-only local speech-to-text dictation tool. It runs as a menu bar app (no Dock icon), listens for a global hotkey (F5), records audio from the microphone, transcribes it locally using Whisper via whisper.cpp, and pastes the result into the focused application.

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

The app has four modules under `whispr/`:

- **main.py** — Entry point. `WhisprApp` subclasses `rumps.App` for the menu bar UI. Registers a global hotkey listener (`pynput`) in a background thread. Toggles recording on F5, Esc/Enter stops recording. Whisper model loads in a background thread on startup (shows "Loading..." in menu bar). Transcription runs in a separate thread to keep the UI responsive.
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
