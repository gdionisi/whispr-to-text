"""Type text into the currently focused application using AppleScript."""

import subprocess


def type_text(text: str):
    """Simulate typing text into the focused app via AppleScript."""
    if not text:
        return

    # Escape for AppleScript string
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')

    script = f'''
    tell application "System Events"
        keystroke "{escaped}"
    end tell
    '''

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        print("Warning: typing timed out")
    except Exception as e:
        print(f"Warning: could not type text: {e}")
