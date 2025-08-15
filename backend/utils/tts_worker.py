from gtts import gTTS
import io
import json
from utils.cache import r

TTS_QUEUE_KEY = "tts_batch_queue"

print("[TTS WORKER] Started")

while True:
    batch = []
    while len(batch) < 5:
        item = r.lpop(TTS_QUEUE_KEY)
        if not item:
            break
        batch.append(json.loads(item))

    if not batch:
        import time
        time.sleep(1)
        continue

    print(f"[TTS WORKER] Processing batch of {len(batch)} items")

    for entry in batch:
        try:
            safe_text = entry["text"].strip().replace("\n", " ")
            tts = gTTS(text=safe_text, lang="en")
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            audio_bytes = buf.getvalue()

            r.setex(entry["key"], entry["ttl"], audio_bytes)
        except Exception as e:
            print(f"[TTS WORKER ERROR] {e}")
