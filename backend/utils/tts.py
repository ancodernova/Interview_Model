from gtts import gTTS
import io
import hashlib
from utils.cache import r
import json

TTS_QUEUE_KEY = "tts_batch_queue"

def queue_tts(question_id, text, ttl=86400):
    """
    Queue TTS generation for async processing.
    """
    key = f"tts:{question_id}"
    if r.get(key):
        return key  # already cached

    r.rpush(TTS_QUEUE_KEY, json.dumps({
        "text": text,
        "key": key,
        "ttl": ttl
    }))
    return key


def get_tts(question_id, text, ttl=86400):
    """
    Synchronous TTS generation (fallback).
    """
    key = f"tts:{question_id}"
    cached_audio = r.get(key)
    if cached_audio:
        return cached_audio

    try:
        safe_text = text.strip().replace("\n", " ")
        tts = gTTS(text=safe_text, lang="en")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        audio_bytes = buf.getvalue()
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return b""

    r.setex(key, ttl, audio_bytes)
    return audio_bytes
