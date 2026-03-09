"""Audio recording from microphone."""

import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1


class Recorder:
    """Records audio from the default microphone."""

    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self):
        """Start recording."""
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            print("🎙 Recording... (press hotkey again to stop)")

    def stop(self) -> np.ndarray:
        """Stop recording and return the audio data."""
        with self._lock:
            if not self._recording:
                return np.array([], dtype=np.float32)
            self._recording = False
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            print("⏹ Recording stopped.")
            if self._frames:
                return np.concatenate(self._frames)
            return np.array([], dtype=np.float32)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio warning: {status}")
        if self._recording:
            self._frames.append(indata.copy().flatten())
