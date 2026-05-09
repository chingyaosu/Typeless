# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Typeless is a macOS menu bar app for push-to-talk voice input. Hold `Option+Space` → speak → release → transcribed and AI-polished text is pasted into the active window.

Pipeline: microphone → Groq Whisper (`whisper-large-v3-turbo`) → Groq LLM (`llama-3.3-70b-versatile`) → clipboard paste via `Cmd+V`.

## Run

```bash
export GROQ_API_KEY=your_key
python3 main.py
```

First-time setup: `bash setup.sh`

## Architecture

| File | Role |
|------|------|
| `main.py` | `rumps` menu bar app, orchestrates all modules |
| `hotkey.py` | CGEventTap-based global hotkey (Option+Space), suppresses the Space keypress so it doesn't leak into the active window |
| `recorder.py` | `sounddevice` audio recording to WAV bytes |
| `api.py` | Groq Whisper transcription + LLM polishing |
| `output.py` | Copies to clipboard via `pbcopy`, pastes via `CGEventPost` Cmd+V |

## Key Design Decisions

**CGEventTap (not pynput):** Required to suppress the Space key event during recording. `pynput` doesn't support per-key suppression on macOS.

**Threading model:**
- Main thread: `rumps` AppKit event loop
- Background thread: CGEventTap `CFRunLoopRun()` (blocks its thread by design)
- On-demand threads: spawned by hotkey callbacks for start/stop (can't block the CGEventTap callback)
- `_lock` in `main.py` prevents overlapping recording sessions

**Output via CGEventPost:** Uses `CGEventPost` to simulate Cmd+V instead of `osascript` — avoids needing Automation permission for every target app. Only Accessibility permission needed.

**Language handling:** The LLM system prompt detects "全中文" / "全英文" prefixes spoken by the user to force language output. Otherwise preserves the original Chinese/English mix from transcription.

## macOS Permissions Required

- **Accessibility** (System Settings > Privacy & Security > Accessibility): needed for CGEventTap to intercept and suppress keys. Grant to Terminal or the launch app.
- **Microphone**: granted on first run by macOS.
