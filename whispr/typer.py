"""Type text into the currently focused application via clipboard paste."""

import subprocess


def type_text(text: str):
    """Copy text to clipboard and paste into the focused app."""
    if not text:
        return

    try:
        # Save current clipboard
        old_clip = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=2
        ).stdout

        # Copy transcribed text to clipboard
        subprocess.run(
            ["pbcopy"], input=text, text=True, timeout=2
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
            ["pbcopy"], input=old_clip, text=True, timeout=2
        )

    except subprocess.TimeoutExpired:
        print("Warning: typing timed out")
    except Exception as e:
        print(f"Warning: could not type text: {e}")
