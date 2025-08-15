import requests
import hashlib
import json
from utils.cache import load_context, r, get_resume_text, save_context
from config import Config
from utils.faiss_index import search_questions
import time

# ===== API Key Rotator =====
# ===== DEDICATED API KEY ROTATORS =====
import time

class APIKeyRotator:
    def __init__(self, api_keys, cooldown_seconds=3600):
        self.api_keys = [key for key in api_keys if key]
        self.index = 0
        self.failed_keys = {}  # {key: timestamp_of_failure}
        self.cooldown_seconds = cooldown_seconds

    def _is_key_available(self, key):
        """Check if key is in cooldown period."""
        if key not in self.failed_keys:
            return True
        last_failed = self.failed_keys[key]
        if time.time() - last_failed > self.cooldown_seconds:
            # Cooldown expired → key is usable again
            del self.failed_keys[key]
            return True
        return False

    def get_key(self):
        """Get the next available key."""
        start_index = self.index
        while True:
            key = self.api_keys[self.index]
            self.index = (self.index + 1) % len(self.api_keys)
            if self._is_key_available(key):
                return key
            # If we’ve looped through all keys and none available
            if self.index == start_index:
                raise RuntimeError("No API keys available (all in cooldown).")

    def mark_key_failed(self, key):
        """Mark a key as failed so it’s skipped temporarily."""
        self.failed_keys[key] = time.time()

# ✅ One rotator per task — unified naming & usage
key_rotator = APIKeyRotator([
    Config.GEMINI_API_KEY,
    Config.GEMINI_API_KEY1,
    Config.GEMINI_API_KEY2,
    Config.GEMINI_API_KEY3,
    Config.GEMINI_API_KEY4,
    Config.GEMINI_API_KEY5,
    Config.GEMINI_API_KEY6,
    Config.GEMINI_API_KEY7,
    Config.GEMINI_API_KEY8,
    Config.GEMINI_API_KEY9,
    Config.GEMINI_API_KEY10,
    Config.GEMINI_API_KEY11,
    Config.GEMINI_API_KEY12,
    Config.GEMINI_API_KEY13,
    Config.GEMINI_API_KEY14
])

# ===== PROMPTS =====

QUESTION_PROMPT = """
Act as a skilled interviewer for service-based companies (TCS, Infosys, Wipro, Accenture) in a 5-stage mock interview:
1. Intro
2–3. Resume-based (follow-ups on last answer or resume)
4. Technical (from FAISS, 1–2 lines, no follow-up)
5. HR scenario

Rules:
- One question at a time.
- For Q1–Q3: Use detail from last answer or resume; if vague, ask for clarification or example.
- For Q4: Rephrase FAISS question to max 2 lines, one concept only.
- For Q5: Ask about teamwork, deadlines, client handling, adaptability.
- Avoid repeats, placeholders, or "Stage X/5" text.
- Keep tone natural, as in a real conversation.

Context:
Resume: {resume_text}
Prev Qs: {previous_questions}
Prev As: {previous_answers}
FAISS Q: {base_question}
Sample Ans: {sample_answer}
Stage: {stage}/5

Return only the question text.
"""


EVALUATION_PROMPT = """
Evaluate 1 interview answer.

Q: {question}
A: {candidate_answer}
Ref: {sample_answer}
Stage: {stage}
Resume: {resume_text}

Rate: technical, completeness, communication, depth, problem-solving (0–10 or null).
Verdict: Needs to learn from scratch | Beginner | Intermediate | Good understanding | Advanced.
List strengths, weaknesses, 1–3 recommendations, and 1-sentence summary.

JSON only:
{{
  "technical_score": number or null,
  "completeness_score": number or null,
  "communication_score": number or null,
  "depth_of_knowledge": number or null,
  "problem_solving_score": number or null,
  "verdict": string or null,
  "strengths": [string],
  "weaknesses": [string],
  "recommendations": [string],
  "summary": string
}}
"""




SUMMARY_PROMPT = """
Prepare final interview report from:
Questions: {questions}
Evaluations: {evaluations}

JSON only:
{{
  "technical_level": "Beginner"|"Intermediate"|"Good understanding"|"Advanced",
  "key_strengths": [string],
  "key_weaknesses": [string],
  "recommended_actions": {{"technical":[string], "soft_skills":[string]}},
  "stage_performance": {{
    "introduction_resume_stage": string,
    "technical_stage": string,
    "hr_stage": string
  }},
  "summary": "21–25 words overview"
}}
"""



# ===== Gemini API Call =====
def _call_gemini(prompt, key_rotator):
    for _ in range(len(key_rotator.api_keys)):
        api_key = key_rotator.get_key()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1500}
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 403 or resp.status_code == 429:
                # Quota exceeded or auth issue → mark failed and try next key
                key_rotator.mark_key_failed(api_key)
                continue
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[Gemini ERROR] Key {api_key} failed: {e}")
            key_rotator.mark_key_failed(api_key)
            continue
    raise RuntimeError("All API keys failed or expired.")


# ===== PUBLIC FUNCTIONS =====
def generate_followup(user_id, user_context, base_question, sample_answer, session_id):
    context = load_context(user_id, session_id)
    resume_text = get_resume_text(user_id) or ""

    previous_questions = context.get("questions", [])
    previous_answers = [a.get("answer", "") for a in context.get("answers", [])]
    stage = len(previous_questions) + 1

    # ✅ Stop after exactly 5 questions
    if stage > 5:
        return None

    # ✅ Stage mapping for 5-question flow
    if stage == 1:
        stage_label = "intro"       # Q1
    elif stage in (2, 3):
        stage_label = "resume"      # Q2–Q3
    elif stage == 4:
        stage_label = "technical"   # Q4
    elif stage == 5:
        stage_label = "hr"          # Q5
    else:
        stage_label = "closing"

    # ✅ Stage 4: Technical — pick from FAISS only, short 1–2 lines, no repeats
    if stage_label == "technical":
        faiss_results = search_questions("technical", k=10)
        asked = set(previous_questions)
        available = [q for q in faiss_results if q.get("question", "") not in asked]

        if not available:
            return None  # No new tech questions available

        import random
        selected = random.choice(available)
        faiss_question = selected.get("question", "").strip()
        faiss_answer = selected.get("answer", "").strip()

        # Shorten to 1–2 lines
        tweak_prompt = f"""
Rewrite the following technical interview question for a service-based company
so it is at most 1–2 lines, asks only ONE thing, and is clear.

Original Question: {faiss_question}
"""
        tweaked_question = _call_gemini(tweak_prompt, key_rotator).strip() or faiss_question

        context["questions"].append(tweaked_question)
        context["sample_answers"].append(faiss_answer)
        save_context(user_id, session_id, context)
        return tweaked_question

    # ✅ For intro, resume, hr — use LLM with cross-questioning
    prompt = QUESTION_PROMPT.format(
        resume_text=resume_text,
        previous_questions=json.dumps(previous_questions, ensure_ascii=False),
        previous_answers=json.dumps(previous_answers, ensure_ascii=False),
        base_question=base_question or "",
        sample_answer=sample_answer or "",
        stage=stage
    )

    cache_key = f"followup:{user_id}:{session_id}:{stage}"
    r.delete(cache_key)  # Force fresh generation
    question = _call_gemini(prompt, key_rotator).strip()
    r.setex(cache_key, 3600, question.encode())

    context["questions"].append(question)
    # Preserve provided sample answer if available
    context["sample_answers"].append(sample_answer or "")
    save_context(user_id, session_id, context)

    return question


def generate_evaluation(question, candidate_answer, sample_answer, stage, resume_text=""):
    prompt = EVALUATION_PROMPT.format(
        question=question,
        candidate_answer=candidate_answer or "",
        sample_answer=sample_answer or "",
        stage=stage,
        resume_text=resume_text
    )

    raw_output = _call_gemini(prompt, key_rotator)

    # Try to parse JSON safely
    try:
        # Remove ```json ``` fences if present
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(line for line in cleaned.splitlines() if not line.strip().startswith("```"))
        return json.loads(cleaned)
    except Exception as e:
        print(f"[Evaluation JSON Parse Error] {e} | Raw: {raw_output}")
        return {
            "technical_score": None,
            "completeness_score": None,
            "communication_score": None,
            "depth_of_knowledge": None,
            "problem_solving_score": None,
            "verdict": None,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "summary": raw_output.strip() if raw_output else ""
        }



def generate_summary(questions, evaluations):
    if not isinstance(evaluations, list) or not evaluations:
        evaluations = []

    prompt = SUMMARY_PROMPT.format(
        questions=json.dumps(questions, ensure_ascii=False),
        evaluations=json.dumps(evaluations, ensure_ascii=False)
    )

    summary_raw = _call_gemini(prompt, key_rotator)

    # Clean ```json fences if present
    cleaned = summary_raw.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(
            line for line in cleaned.splitlines()
            if not line.strip().startswith("```")
        )

    # Try to parse JSON
    try:
        summary_json = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"[Summary JSON Parse Error] Raw Output: {cleaned}")
        summary_json = {
            "technical_level": None,
            "key_strengths": [],
            "key_weaknesses": [],
            "recommended_actions": {"technical": [], "soft_skills": []},
            "stage_performance": {},
            "summary": str(cleaned)
        }

    # Ensure summary length is 21–25 words
    if isinstance(summary_json.get("summary"), str):
        words = summary_json["summary"].split()
        if len(words) > 25:
            summary_json["summary"] = " ".join(words[:25])
        elif len(words) < 21 and words:
            summary_json["summary"] += " " + " ".join([words[-1]] * (21 - len(words)))
    else:
        summary_json["summary"] = ""

    return summary_json
