#!/usr/bin/env python3
"""
Typeless — Push-to-talk voice input for macOS
Hold Option+Space → speak → release → text appears in active window.
"""

import os
import subprocess
import threading

# Load ~/.typeless_env before anything else (needed when launched from Finder)
_env_file = os.path.expanduser("~/.typeless_env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

import rumps
from AppKit import NSWorkspace

from api import detect_command, is_hallucination, polish, transcribe
from hotkey import HotkeyListener
from output import execute_command, paste_text
from recorder import AudioRecorder
from status_window import StatusWindow

ICON_IDLE = "⌨️"
ICON_RECORDING = "🔴"
ICON_PROCESSING = "⏳"

import ctypes
from ctypes import c_uint32, c_void_p, c_char_p

# AudioServices — lowest-latency system sound API, thread-safe
_audio = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/AudioToolbox.framework/AudioToolbox"
)
_cf = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
)
_audio.AudioServicesCreateSystemSoundID.argtypes = [c_void_p, ctypes.POINTER(c_uint32)]
_audio.AudioServicesPlaySystemSound.argtypes = [c_uint32]
_cf.CFURLCreateFromFileSystemRepresentation.restype = c_void_p


def _load_sound(path: str) -> int:
    url = _cf.CFURLCreateFromFileSystemRepresentation(
        None, path.encode("utf-8"), len(path), False
    )
    sound_id = c_uint32()
    _audio.AudioServicesCreateSystemSoundID(url, ctypes.byref(sound_id))
    return sound_id.value


_SOUNDS = {
    "start": _load_sound("/System/Library/Sounds/Tink.aiff"),
    "done": _load_sound("/System/Library/Sounds/Pop.aiff"),
    "cmd": _load_sound("/System/Library/Sounds/Morse.aiff"),
}

SOUND_START = "start"
SOUND_DONE = "done"
SOUND_CMD = "cmd"


_SOUND_FILES = {
    "start": "/System/Library/Sounds/Tink.aiff",
    "done": "/System/Library/Sounds/Pop.aiff",
    "cmd": "/System/Library/Sounds/Morse.aiff",
}


def play(sound_key: str):
    sid = _SOUNDS.get(sound_key)
    if sid:
        _audio.AudioServicesPlaySystemSound(sid)
    # Fallback: also spawn afplay in case AudioServices is silent in this context
    f = _SOUND_FILES.get(sound_key)
    if f:
        subprocess.Popen(["afplay", f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_active_app() -> str:
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return app.localizedName() if app else ""


class TypelessApp(rumps.App):
    def __init__(self):
        super().__init__(ICON_IDLE, quit_button="Quit Typeless")
        self.menu = ["Option+Space: push-to-talk", None]

        self._recorder = AudioRecorder()
        # Pick one: "capsule" (minimal pill) | "card" (big emoji) | "bubble" (illustrated face)
        self._status = StatusWindow(style=os.environ.get("PANDA_STYLE", "capsule"))
        self._busy = False
        self._active_app = ""

        hotkey = HotkeyListener(
            on_start=self._on_start,
            on_stop=self._on_stop,
            on_press_immediate=lambda: play(SOUND_START),
        )
        hotkey.start()

    def _on_start(self):
        if self._busy:
            return
        self._busy = True
        try:
            self._active_app = get_active_app()
            self.title = ICON_RECORDING
            self._status.show_recording()
            self._recorder.start()
        except Exception as e:
            print(f"[Typeless] start error: {e}")
            self.title = ICON_IDLE
            self._busy = False

    def _on_stop(self):
        if not self._busy:
            return
        try:
            audio = self._recorder.stop()
            play(SOUND_DONE)

            if not audio:
                self._status.hide()
                return

            self.title = ICON_PROCESSING
            self._status.show_analyzing()
            raw = transcribe(audio)
            print(f"[Typeless] raw: {raw!r}", flush=True)
            if not raw:
                self._status.hide()
                return

            if is_hallucination(raw):
                print(f"[Typeless] dropped (hallucination)", flush=True)
                self._status.hide()
                return

            command = detect_command(raw)
            print(f"[Typeless] command: {command}", flush=True)
            if command:
                play(SOUND_CMD)
                execute_command(command)
                self._status.show_text(f"⌘ {command}")
                return

            polished = polish(raw, app_name=self._active_app)
            paste_text(polished)
            self._status.show_text(polished)

        except Exception as e:
            print(f"[Typeless] Error: {e}")
            self._status.hide()
        finally:
            self.title = ICON_IDLE
            self._busy = False


def check_api_key():
    if not os.environ.get("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set.\nRun: export GROQ_API_KEY=your_key_here")
        raise SystemExit(1)


def request_microphone():
    """Trigger macOS microphone permission dialog if not yet granted."""
    try:
        from AVFoundation import AVCaptureDevice
        # AVMediaTypeAudio = "soun"
        status = AVCaptureDevice.authorizationStatusForMediaType_("soun")
        print(f"[Typeless] Microphone status: {status} (3 = authorized)")
        if status == 0:  # NotDetermined → request
            done = threading.Event()
            def cb(granted):
                print(f"[Typeless] Microphone granted: {granted}")
                done.set()
            AVCaptureDevice.requestAccessForMediaType_completionHandler_("soun", cb)
            done.wait(timeout=30)
    except Exception as e:
        print(f"[Typeless] Microphone request failed: {e}")


def request_accessibility():
    """Check Accessibility permission for THIS process."""
    import ctypes, sys
    ax = ctypes.cdll.LoadLibrary(
        "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
    )
    ax.AXIsProcessTrusted.restype = ctypes.c_bool
    trusted = ax.AXIsProcessTrusted()
    print(f"[Typeless] Process: {sys.executable}", flush=True)
    print(f"[Typeless] Accessibility: {'✅ AUTHORIZED' if trusted else '❌ NOT AUTHORIZED'}", flush=True)
    return trusted


if __name__ == "__main__":
    check_api_key()
    request_microphone()
    if not request_accessibility():
        print("⚠️  請在系統設定 > 輔助使用 中授權，然後重新啟動 Typeless")
    TypelessApp().run()
