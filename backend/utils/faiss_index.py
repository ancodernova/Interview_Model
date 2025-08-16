import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from prisma import Prisma   # ✅ Prisma client instead of SQLAlchemy
from flask import current_app

# ===== Embedding Model =====
model = SentenceTransformer("all-MiniLM-L6-v2")

# ===== Question Bank Index =====
QUESTION_INDEX_PATH = "embeddings/question_index.faiss"
QUESTION_DATA_PATH = "embeddings/question_data.json"

def load_question_index():
    if not os.path.exists(QUESTION_INDEX_PATH) or not os.path.exists(QUESTION_DATA_PATH):
        return None, []
    index = faiss.read_index(QUESTION_INDEX_PATH)
    with open(QUESTION_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return index, data

question_index, question_data = load_question_index()

def search_questions(query, k=3):
    """Search similar questions from global FAISS question bank"""
    if not question_index:
        return []
    vec = model.encode([query], convert_to_numpy=True)
    D, I = question_index.search(vec, k)
    return [question_data[i] for i in I[0] if i < len(question_data)]


# ===== Resume Index =====
RESUME_INDEX_DIR = "embeddings/resumes"
os.makedirs(RESUME_INDEX_DIR, exist_ok=True)

def build_resume_index(user_id, resume_text):
    """Create or overwrite FAISS index for this user's resume"""
    user_dir = os.path.join(RESUME_INDEX_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    sentences = [s.strip() for s in resume_text.split("\n") if s.strip()]
    if not sentences:
        return

    embeddings = model.encode(sentences, convert_to_numpy=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, os.path.join(user_dir, "resume_index.faiss"))
    with open(os.path.join(user_dir, "resume_data.json"), "w", encoding="utf-8") as f:
        json.dump([{"question": s} for s in sentences], f, ensure_ascii=False, indent=2)

def search_resume(user_id, query, k=3):
    """Search inside a user's FAISS resume index"""
    user_dir = os.path.join(RESUME_INDEX_DIR, str(user_id))
    idx_path = os.path.join(user_dir, "resume_index.faiss")
    data_path = os.path.join(user_dir, "resume_data.json")

    if not os.path.exists(idx_path) or not os.path.exists(data_path):
        return []

    index = faiss.read_index(idx_path)
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    vec = model.encode([query], convert_to_numpy=True)
    D, I = index.search(vec, k)
    return [data[i] for i in I[0] if i < len(data)]


# ===== Resume Fetch via Prisma =====
async def get_resume_from_db(user_id: int):
    """Fetch resume_text from Prisma DB (Railway PostgreSQL)"""
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"id": user_id})
    await prisma.disconnect()

    if user and user.resumeText:
        return user.resumeText
    return None
