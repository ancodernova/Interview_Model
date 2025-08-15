import whisper
import os
import json
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.cache import r

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
model = whisper.load_model(WHISPER_MODEL_SIZE)
STT_QUEUE_KEY = "stt_batch_queue"

MAX_WORKERS = int(os.getenv("STT_WORKERS", 4))  # configurable parallel threads
BATCH_SIZE = 5  # how many to fetch from Redis per loop

print(f"[STT WORKER] Started with model {WHISPER_MODEL_SIZE} using {MAX_WORKERS} threads")

def process_entry(entry):
    """Handles transcription of a single entry"""
    tmp_path = None
    try:
        audio_bytes = bytes.fromhex(entry["audio_bytes"])
        tmp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        with open(tmp_path, "wb") as f:
            f.write(audio_bytes)

        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        if text:
            r.setex(entry["key"], entry["ttl"], text.encode())
        return entry["key"], text

    except Exception as e:
        print(f"[STT WORKER ERROR] {e}")
        return entry["key"], None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass

while True:
    batch = []
    while len(batch) < BATCH_SIZE:
        item = r.lpop(STT_QUEUE_KEY)
        if not item:
            break
        batch.append(json.loads(item))

    if not batch:
        time.sleep(1)
        continue

    print(f"[STT WORKER] Processing batch of {len(batch)} items...")

    # Process in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_entry, entry): entry for entry in batch}

        for future in as_completed(futures):
            key, text = future.result()
            print(f"[STT WORKER] Completed {key}: {bool(text)}")
