# Whispr

Local speech-to-text dictation for macOS. Press a hotkey, speak, and your words are typed into the focused application. Transcription runs entirely on your machine using [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — no internet connection or API key needed.

## Setup

```bash
# Clone and install
git clone https://github.com/gdionisi/whispr-to-text.git
cd whispr-to-text
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Requires Python 3.11+.

## First launch

```bash
whispr
```

On the first run, the Whisper "small" model (~466 MB) is automatically downloaded. The menu bar will show **"Loading..."** while the model loads. Once it disappears, Whispr is ready.

The model is cached by `pywhispercpp` so subsequent launches are fast.

## macOS permissions

Whispr requires two permissions in **System Settings → Privacy & Security**:

| Permission | Why | Where to grant |
|---|---|---|
| **Accessibility** | Global hotkey detection and simulating Cmd+V to paste text | Privacy & Security → Accessibility |
| **Microphone** | Recording audio for transcription | Privacy & Security → Microphone |

You will be prompted automatically the first time. If Whispr doesn't respond to hotkeys or can't record, check these settings.

> **Tip:** If you run Whispr from a terminal (e.g., iTerm, Terminal.app), you need to grant permissions to **that terminal app**, not to Python or Whispr directly.

## Usage

1. Press **F5** (default) to start recording — the menu bar icon turns 🔴
2. Speak into your microphone
3. Press **Escape** or **Return** (default) to stop recording — the icon turns ⏳ while transcribing
4. The transcribed text is automatically pasted into the focused application

You can also toggle recording from the menu bar dropdown.

## Configuring hotkeys

Hotkeys are configurable directly from the menu bar:

1. Click the Whispr menu bar icon
2. Click **"Toggle Key: ..."** or **"Stop Key: ..."**
3. The menu bar shows ⌨️ — press your desired key or key combo (e.g., `Cmd+Shift+R`)
4. The new binding is saved immediately

Use **"Reset Key Bindings"** to restore defaults (F5 to toggle, Escape/Return to stop).

Settings are stored in `~/Library/Application Support/Whispr/config.json`.

## Building the .app bundle

To create a standalone macOS application:

```bash
pip install pyinstaller
pyinstaller whispr.spec
```

The app is output to `dist/Whispr.app`. You can drag it to your Applications folder.
