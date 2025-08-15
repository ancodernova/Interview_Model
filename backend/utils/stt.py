import whisper
import tempfile
import hashlib
from utils.cache import r
import os
import json

# Load Whisper model only in worker process
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

# Redis queue key
STT_QUEUE_KEY = "stt_batch_queue"

def queue_audio_for_transcription(audio_bytes, ttl=3600):
    """
    Push audio to Redis queue for async batch STT.
    Returns cache key so caller can poll for result.
    """
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    key = f"stt:{audio_hash}"

    # If already cached, return immediately
    cached_text = r.get(key)
    if cached_text:
        return key, cached_text.decode()

    # Add to queue
    r.rpush(STT_QUEUE_KEY, json.dumps({
        "audio_bytes": audio_bytes.hex(),  # store as hex string for Redis
        "key": key,
        "ttl": ttl
    }))

    return key, None  # Not ready yet


def transcribe_audio(audio_bytes, ttl=3600):
    """
    Synchronous STT (no batching) — fallback if no worker.
    """
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    key = f"stt:{audio_hash}"

    cached_text = r.get(key)
    if cached_text:
        return cached_text.decode()

    tmp_path = None
    text = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = whisper.load_model(WHISPER_MODEL_SIZE)
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()

    except Exception as e:
        print(f"[STT ERROR] Failed to transcribe: {e}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    if text:
        r.setex(key, ttl, text.encode())

    return text
