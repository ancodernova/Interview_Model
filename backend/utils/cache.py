import redis
import os
import json
import hashlib
import faiss
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer
from prisma import Prisma  

# ===== Redis Connection =====
redis_url = os.getenv("REDIS_URL")
if redis_url:
    url = urlparse(redis_url)
    r = redis.Redis(
        host=url.hostname,
        port=url.port,
        password=url.password,
        ssl=True if url.scheme == "rediss" else False,
        decode_responses=False
    )
else:
    # Local fallback
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=False
    )

# ===== Paths =====
RESUME_DIR = "embeddings/resumes"
os.makedirs(RESUME_DIR, exist_ok=True)

# ===== Embedding Model =====
model = SentenceTransformer("all-MiniLM-L6-v2")

# ===== Conversation Context =====
def context_key(user_id, session_id):
    return f"ctx:{user_id}:{session_id}"

def load_context(user_id, session_id):
    data = r.get(context_key(user_id, session_id))
    return json.loads(data) if data else {
        "topics": [],
        "questions": [],
        "sample_answers": [],
        "evaluations": [],
        "answers": [],
        "question_count": 0,
        "stage": "intro"
    }

def save_context(user_id, session_id, context, ttl=86400):
    r.setex(context_key(user_id, session_id), ttl, json.dumps(context))

# ===== Session-Aware Cache for LLM Outputs =====
def get_cached_llm_result(prefix, prompt, session_id=None, ttl=3600):
    """Cache LLM results keyed by prompt hash (and session if provided)."""
    raw_key = prompt + (str(session_id) if session_id else "")
    prompt_hash = hashlib.md5(raw_key.encode()).hexdigest()
    key = f"{prefix}:{prompt_hash}"
    cached = r.get(key)
    return cached.decode() if cached else None

def set_cached_llm_result(prefix, prompt, result, session_id=None, ttl=3600):
    raw_key = prompt + (str(session_id) if session_id else "")
    prompt_hash = hashlib.md5(raw_key.encode()).hexdigest()
    key = f"{prefix}:{prompt_hash}"
    r.setex(key, ttl, result.encode())

# ===== Anti-Script Detection =====
def is_scripted_answer(candidate_answer, sample_answer, threshold=0.85):
    """
    Checks if candidate answer is too similar to sample answer.
    Uses simple cosine similarity on hashed values for caching.
    """
    from difflib import SequenceMatcher

    cache_key = f"script_check:{hashlib.md5((candidate_answer+sample_answer).encode()).hexdigest()}"
    cached = r.get(cache_key)
    if cached:
        return cached.decode() == "true"

    ratio = SequenceMatcher(None, candidate_answer.lower(), sample_answer.lower()).ratio()
    scripted = ratio >= threshold

    r.setex(cache_key, 3600, b"true" if scripted else b"false")
    return scripted

# ===== TTS/STT Caching =====
def get_cached_audio(key):
    return r.get(key)

def set_cached_audio(key, audio_bytes, ttl=86400):
    r.setex(key, ttl, audio_bytes)

def get_cached_transcription(audio_hash):
    cached = r.get(f"stt:{audio_hash}")
    return cached.decode() if cached else None

def set_cached_transcription(audio_hash, text, ttl=3600):
    r.setex(f"stt:{audio_hash}", ttl, text.encode())

# ===== Resume Caching & Embeddings =====
async def get_resume_text(user_id: int):
    """
    Fetch resume text from Redis first, then DB via Prisma if missing.
    Cache it in Redis for 24 hours.
    """
    key = f"resume:{user_id}"
    data = r.get(key)
    if data:
        return data.decode()

    await prisma.connect()
    user = await prisma.user.find_unique(where={"id": user_id})
    await prisma.disconnect()

    if user and user.resumeText:
        r.setex(key, 86400, user.resumeText)
        return user.resumeText
    return None

def store_resume_embedding(user_id, resume_text):
    """
    Store per-user FAISS index for resume lines.
    """
    index_path = os.path.join(RESUME_DIR, f"{user_id}.faiss")
    data_path = os.path.join(RESUME_DIR, f"{user_id}.json")

    if os.path.exists(index_path) and os.path.exists(data_path):
        return  # already stored

    sentences = [line.strip() for line in resume_text.split("\n") if line.strip()]
    if not sentences:
        return

    embeddings = model.encode(sentences, convert_to_numpy=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, index_path)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump([{"id": i, "question": s, "answer": ""} for i, s in enumerate(sentences)], f)

# ===== Session Cleanup =====
def cleanup_session_cache(user_id, session_id, keep_fields=None):
    """
    Deletes all cached data for a given session except specified keys.
    Decodes Redis keys to str before matching, to avoid TypeError.
    """
    if keep_fields is None:
        keep_fields = []

    # Delete session context
    r.delete(f"ctx:{user_id}:{session_id}")

    # Helper: check if key should be kept
    def should_keep(key):
        key_str = key.decode() if isinstance(key, bytes) else key
        return any(field in key_str for field in keep_fields)

    # Delete followup question caches
    for key in r.scan_iter(f"followup:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)

    # Delete evaluation caches
    for key in r.scan_iter(f"eval:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)

    # Delete generated questions & sample answers
    for key in r.scan_iter(f"questions:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)
    for key in r.scan_iter(f"sample_answers:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)

    # Delete any TTS/STT audio for this session
    for key in r.scan_iter(f"stt:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)
    for key in r.scan_iter(f"tts:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)

    # Delete any cached audio for this session
    for key in r.scan_iter(f"audio:{user_id}:{session_id}:*"):
        if not should_keep(key):
            r.delete(key)

def get_all_cached_evaluations(user_id, session_id):
        keys = r.keys(f"evaluation:{user_id}:{session_id}:*")
        evals = []
        for k in keys:
            try:
                evals.append(json.loads(r.get(k)))
            except:
                pass
        return evals
        
