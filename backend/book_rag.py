import os
import json
import faiss
import pdfplumber
import re
from sentence_transformers import SentenceTransformer
from uuid import uuid4

# ===== Paths =====
PDF_FILES = [
    r"C:\Users\Aniket\OneDrive\Desktop\Model2\backend\bank\OOPS Principles in JAVA.pdf",
    r"C:\Users\Aniket\OneDrive\Desktop\Model2\backend\bank\dbms and sql interview prep.pdf",
    r"C:\Users\Aniket\OneDrive\Desktop\Model2\backend\bank\25 JAVA specific questions for interviews.pdf",
    r"C:\Users\Aniket\OneDrive\Desktop\Model2\backend\bank\python interview questions.pdf"
]

OUTPUT_JSON = "embeddings/question_data.json"
OUTPUT_INDEX = "embeddings/question_index.faiss"

# ===== Embedding Model =====
model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_qa_from_pdf(pdf_path):
    """
    Extract Q&A pairs from PDFs with format-specific logic.
    Supports:
    - "Question:" / "Answer:"
    - "Q1.", "Q2", "Q:"
    - Numbered (1., 2.) without explicit 'Answer:'
    """
    filename = os.path.basename(pdf_path).lower()
    qa_pairs = []

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        lines = [line.strip() for line in text.split("\n") if line.strip()]

    current_q, current_a = "", ""

    # ===== OOPS + Python (explicit "Question:" / "Answer:")
    if "oops" in filename or "python" in filename:
        for line in lines:
            if re.match(r"^(question|q\d*[:.]?)", line.lower()):
                if current_q and current_a:
                    qa_pairs.append({
                        "id": str(uuid4()),
                        "question": current_q.strip(),
                        "answer": current_a.strip(),
                        "source": os.path.basename(pdf_path)
                    })
                    current_a = ""
                current_q = re.sub(r"^(question|q\d*[:.]?)", "", line, flags=re.I).strip()

            elif re.match(r"^(answer|ans)[:.]?", line.lower()):
                current_a = re.sub(r"^(answer|ans)[:.]?", "", line, flags=re.I).strip()

            else:
                if current_a:
                    current_a += " " + line
                elif current_q:
                    current_q += " " + line

        if current_q and current_a:
            qa_pairs.append({
                "id": str(uuid4()),
                "question": current_q.strip(),
                "answer": current_a.strip(),
                "source": os.path.basename(pdf_path)
            })

    # ===== DBMS + 25 Java (numbered without "Answer:" labels)
    else:
        q_pattern = re.compile(r"^\d+\.\s")  # matches "1. ", "2. "
        for line in lines:
            if q_pattern.match(line):
                if current_q and current_a:
                    qa_pairs.append({
                        "id": str(uuid4()),
                        "question": current_q.strip(),
                        "answer": current_a.strip(),
                        "source": os.path.basename(pdf_path)
                    })
                    current_a = ""
                current_q = q_pattern.sub("", line).strip()
            else:
                if not current_a and current_q:
                    current_a = line
                elif current_a:
                    current_a += " " + line

        if current_q and current_a:
            qa_pairs.append({
                "id": str(uuid4()),
                "question": current_q.strip(),
                "answer": current_a.strip(),
                "source": os.path.basename(pdf_path)
            })

    return qa_pairs


def book_rag():
    all_data = []

    for pdf in PDF_FILES:
        if os.path.exists(pdf):
            qa_pairs = extract_qa_from_pdf(pdf)
            if qa_pairs:
                all_data.extend(qa_pairs)
                print(f"✅ Extracted {len(qa_pairs)} Q&A pairs from {os.path.basename(pdf)}")
                # Preview first 2 for verification
                for sample in qa_pairs[:2]:
                    print(f"   Q: {sample['question'][:80]}...")
                    print(f"   A: {sample['answer'][:80]}...")
            else:
                print(f"⚠ No Q&A pairs found in {os.path.basename(pdf)}")
        else:
            print(f"❌ File not found: {pdf}")

    if not all_data:
        raise ValueError("❌ No questions extracted from any PDF.")

    questions = [item["question"] for item in all_data]
    embeddings = model.encode(questions, convert_to_numpy=True)

    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise ValueError("❌ No valid embeddings generated. Check input questions.")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    os.makedirs("embeddings", exist_ok=True)
    faiss.write_index(index, OUTPUT_INDEX)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Indexed {len(all_data)} questions into FAISS.")


if __name__ == "__main__":
    book_rag()
