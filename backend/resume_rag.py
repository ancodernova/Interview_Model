# backend/resume_rag.py
import os
import faiss
import json
from sentence_transformers import SentenceTransformer
from utils.cache import r  # optional cache
from models import db, User
import numpy as np

RESUME_EMB_DIR = "embeddings/resumes"
os.makedirs(RESUME_EMB_DIR, exist_ok=True)

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_resume_index(user_id, resume_text):
    """
    Create/update FAISS index for a user's resume text
    """
    if not resume_text.strip():
        raise ValueError("Resume text is empty")

    # Split into smaller chunks for better search
    chunks = [resume_text[i:i+400] for i in range(0, len(resume_text), 400)]

    embeddings = model.encode(chunks, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save FAISS + metadata
    faiss.write_index(index, os.path.join(RESUME_EMB_DIR, f"resume_{user_id}.faiss"))
    with open(os.path.join(RESUME_EMB_DIR, f"resume_{user_id}.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Resume FAISS index built for user {user_id} with {len(chunks)} chunks")


def search_resume_context(user_id, query, k=3):
    """
    Search user's resume index for relevant context
    """
    faiss_path = os.path.join(RESUME_EMB_DIR, f"resume_{user_id}.faiss")
    json_path = os.path.join(RESUME_EMB_DIR, f"resume_{user_id}.json")

    if not os.path.exists(faiss_path) or not os.path.exists(json_path):
        return []

    index = faiss.read_index(faiss_path)
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    query_emb = model.encode([query], convert_to_numpy=True)
    D, I = index.search(query_emb, k)
    results = [chunks[i] for i in I[0] if i < len(chunks)]
    return results
