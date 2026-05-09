import io
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# App name → tone instruction
APP_TONES = {
    # Chat / messaging
    "Slack": "casual and conversational, short sentences, emoji is fine",
    "Messages": "casual, very short",
    "Discord": "casual, short",
    "LINE": "casual, short",
    "WeChat": "casual, short",
    # Email
    "Mail": "professional and formal, well-structured",
    "Microsoft Outlook": "professional and formal, well-structured",
    # Notes / docs
    "Notion": "clear and structured",
    "Obsidian": "clear and structured, use markdown if helpful",
    "Microsoft Word": "formal and well-structured",
    "Notes": "natural, personal",
    "Google Docs": "clear and structured",
    # Code / dev tools — don't touch technical terms
    "Visual Studio Code": "technical, preserve all code/technical terms exactly as spoken",
    "Xcode": "technical, preserve all code/technical terms exactly as spoken",
    "Terminal": "technical, concise, preserve commands exactly",
    "PyCharm CE": "technical, preserve all code/technical terms exactly as spoken",
}

BASE_SYSTEM = """You are a voice transcription polisher. Rules:
- Fix obvious speech recognition errors and add appropriate punctuation
- Preserve original language mixing (Chinese/English exactly as spoken)
- Remove filler words (嗯、啊、那個、um、uh) unless they carry meaning
- Do NOT change meaning, do NOT restructure sentences
- If text starts with "全中文", translate everything to Traditional Chinese and remove that prefix
- If text starts with "全英文" or "all English", translate everything to English and remove that prefix
- Return ONLY the polished text, no explanations"""

# Commands that trigger keyboard shortcuts instead of pasting text
# Key: set of phrases, Value: command name
VOICE_COMMANDS: list[tuple[set[str], str]] = [
    ({"重新說", "重來", "刪掉", "刪除", "再說一次", "undo"}, "undo"),
    ({"全選", "select all"}, "select_all"),
    ({"換行", "new line", "newline"}, "newline"),
    ({"送出", "傳送", "發送", "送", "send"}, "send"),
    ({"複製", "copy"}, "copy"),
    ({"剪下", "cut"}, "cut"),
]


def detect_command(text: str) -> str | None:
    normalized = text.strip().lower().rstrip("。，.!！?？ ")
    # Exact match first
    for phrases, command in VOICE_COMMANDS:
        if normalized in phrases:
            return command
    # Fuzzy match: only treat as command if the whole utterance is short (<10 chars)
    # to avoid misfiring on long sentences containing the command word.
    if len(normalized) <= 10:
        for phrases, command in VOICE_COMMANDS:
            for p in phrases:
                if p in normalized:
                    return command
    return None


# Common Whisper hallucinations on silent/short audio (YouTube subtitle training artifacts)
HALLUCINATIONS = {
    "thank you", "thanks for watching", "thank you for watching",
    "謝謝觀看", "謝謝觀看,下次見", "謝謝觀看,下次見!",
    "下次見", "感謝您的觀看", "感謝觀看",
    "全文字幕由 amara.org 社群提供",
    "字幕由 amara.org 社群提供",
    "字幕製作", "字幕製作:",
    "中文字幕", "繁體字幕",
    "請訂閱我的頻道", "請按讚訂閱",
    "ご視聴ありがとうございました",
    "you", ".", "。", "?", "？", "!", "！",
}


def is_hallucination(text: str) -> bool:
    t = text.strip().lower().rstrip("。，.!！?？ ")
    return t in HALLUCINATIONS or any(h in t for h in [
        "amara.org", "字幕由", "字幕製作", "subscribe to my channel",
    ])


def transcribe(audio_bytes: bytes) -> str:
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"
    result = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=audio_file,
        response_format="text",
        language="zh",  # zh mode preserves English words; avoids Korean/Japanese/Swedish misfires
        prompt=(
            "這是一段中英混合 (Chinese and English mixed) 的語音輸入。"
            "常用指令：送出、傳送、重新說、全選、換行、複製、剪下。"
            "Common English: send, undo, copy, paste, new line."
        ),
    )
    return result.strip()


def polish(text: str, app_name: str = "") -> str:
    if not text:
        return text

    tone = APP_TONES.get(app_name, "neutral and natural")
    system = BASE_SYSTEM + f"\n- Tone: {tone} (current app: {app_name or 'unknown'})"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()
