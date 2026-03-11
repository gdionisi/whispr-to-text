"""Whisper transcription using whisper.cpp."""

from pywhispercpp.model import Model

_model: Model | None = None


def load_model(model_size: str = "small") -> Model:
    """Load the Whisper model (downloads on first use)."""
    global _model
    if _model is None:
        print(f"Loading Whisper '{model_size}' model (first run downloads ~466MB)...")
        _model = Model(model_size, print_progress=False)
        print("Model loaded.")
    return _model


def transcribe(audio_data, sample_rate: int = 16000, language: str = "en") -> str:
    """Transcribe audio numpy array to text."""
    import numpy as np

    model = load_model()

    # Ensure float32, mono, 16kHz
    audio = np.array(audio_data, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # Resample if needed
    if sample_rate != 16000:
        from fractions import Fraction
        ratio = Fraction(16000, sample_rate)
        n_samples = int(len(audio) * ratio)
        indices = np.linspace(0, len(audio) - 1, n_samples)
        audio = np.interp(indices, np.arange(len(audio)), audio)

    segments = model.transcribe(audio, language=language)
    text = " ".join(seg.text for seg in segments).strip()
    return text
