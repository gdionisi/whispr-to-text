"""Type text into the currently focused application via clipboard paste."""

import os
import subprocess

# When launched from an .app bundle, LANG may not be set, causing pbcopy/pbpaste
# to interpret UTF-8 bytes as Mac Roman. Force a UTF-8 locale for subprocesses.
_ENV = {**os.environ, "LANG": "en_US.UTF-8"}


def type_text(text: str):
    """Copy text to clipboard and paste into the focused app."""
    if not text:
        return

    try:
        # Save current clipboard
        old_clip = subprocess.run(
            ["pbpaste"], capture_output=True, encoding="utf-8", timeout=2,
            env=_ENV,
        ).stdout

        # Copy transcribed text to clipboard
        subprocess.run(
            ["pbcopy"], input=text, encoding="utf-8", timeout=2,
            env=_ENV,
        )

        # Cmd+V to paste into focused app
        script = '''
        tell application "System Events"
            keystroke "v" using command down
        end tell
        '''
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Restore previous clipboard after a short delay
        subprocess.run(
            ["pbcopy"], input=old_clip, encoding="utf-8", timeout=2,
            env=_ENV,
        )

    except subprocess.TimeoutExpired:
        print("Warning: typing timed out")
    except Exception as e:
        print(f"Warning: could not type text: {e}")
