import io
import time
import wave
import threading
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
MIN_DURATION = 0.4  # seconds
MIN_RMS = 200  # int16 RMS threshold — below this is treated as silence (no speech)


class AudioRecorder:
    """
    Keeps the InputStream open the whole time the app is running so it doesn't
    have to grab/release the audio session on every press (which would block
    other audio output like our start sound).
    """

    def __init__(self):
        self._frames = []
        self._lock = threading.Lock()
        self._capturing = False
        self._start_time = None
        self._stream = None
        self._open_stream()

    def _open_stream(self):
        # Reset Portaudio so it picks up the current default device after
        # headphone unplug / Bluetooth switch (which is what causes -50 errors).
        try:
            sd._terminate()
            sd._initialize()
        except Exception as e:
            print(f"[recorder] reinit warn: {e}", flush=True)
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=self._callback,
            blocksize=1024,
        )
        self._stream.start()
        print(f"[recorder] stream opened", flush=True)

    def _ensure_stream(self):
        """Reopen the stream if it died (CoreAudio -50 after device change)."""
        try:
            if self._stream is None or not self._stream.active:
                print(f"[recorder] stream inactive, reopening", flush=True)
                try:
                    if self._stream is not None:
                        self._stream.close()
                except Exception:
                    pass
                self._open_stream()
        except Exception as e:
            print(f"[recorder] ensure_stream error: {e}, reopening", flush=True)
            self._open_stream()

    def _callback(self, indata, frames, time_info, status):
        if self._capturing:
            with self._lock:
                self._frames.append(indata.copy())

    def start(self):
        self._ensure_stream()
        with self._lock:
            self._frames = []
        self._start_time = time.time()
        self._capturing = True

    def stop(self) -> bytes | None:
        self._capturing = False
        elapsed = time.time() - self._start_time if self._start_time else 0

        if elapsed < MIN_DURATION:
            return None

        with self._lock:
            if not self._frames:
                return None
            audio = np.concatenate(self._frames, axis=0)

        # Energy check: skip if too quiet (prevents Whisper hallucinations)
        rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
        print(f"[recorder] duration={elapsed:.2f}s rms={rms:.0f}", flush=True)
        if rms < MIN_RMS:
            return None

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()
