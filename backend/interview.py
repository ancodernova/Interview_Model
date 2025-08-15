from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, InterviewSession, InterviewQuestion, User
from utils.faiss_index import search_questions, search_resume, build_resume_index
from utils.tts import get_tts
from utils.stt import transcribe_audio
from utils.llm import generate_followup, generate_summary, generate_evaluation, _call_gemini,key_rotator
from utils.cache import r, is_scripted_answer, cleanup_session_cache
import json
import hashlib
import pdfplumber
import re

interview_bp = Blueprint("interview", __name__)

# ===== Helper functions for Redis context =====
def _context_key(user_id, session_id):
    return f"ctx:{user_id}:{session_id}"

def _load_context(user_id, session_id):
    data = r.get(_context_key(user_id, session_id))
    return json.loads(data) if data else {
        "topics": [],
        "questions": [],
        "sample_answers": [],
        "evaluations": [],
        "answers": [],
        "question_count": 0,
        "stage": "intro"
    }

def _save_context(user_id, session_id, context):
    r.setex(_context_key(user_id, session_id), 86400, json.dumps(context))  # 1 day TTL

def _get_stage(q_count):

    """
    Map question count to interview stage.
    """
    if q_count == 1:
        return "intro"
    elif 2 <= q_count <= 3:
        return "resume"
    elif 4:
        return "technical"
    else:
        return "closing"

# ===== Start Interview =====
@interview_bp.route("/start", methods=["POST"])
@jwt_required()
def start_interview():
    user_id = int(get_jwt_identity())
    session = InterviewSession(user_id=user_id)
    db.session.add(session)
    db.session.commit()

    _save_context(user_id, session.id, {
        "topics": [],
        "questions": [],
        "sample_answers": [],
        "evaluations": [],
        "answers": [],
        "question_count": 0,
        "stage": "intro"
    })

    return jsonify({"session_id": session.id})

# ===== Ask Question =====

@interview_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask_question():
    data = request.get_json()
    topic = data.get("topic")
    session_id = data.get("session_id")
    user_id = int(get_jwt_identity())

    if not session_id or not topic:
        return jsonify({"error": "session_id and topic are required"}), 400

    # Load context
    context = _load_context(user_id, session_id)
    q_count = context.get("question_count", 0)

    # ✅ Stop after exactly 5 questions
    if q_count >= 5:
        return jsonify({"done": True, "message": "Interview completed"}), 200

    stage = _get_stage(q_count)
    question_text = ""
    sample_answer = ""

    try:
        # Always route through generate_followup (handles FAISS for technical stage)
        question_text = generate_followup(
            user_id=user_id,
            user_context=json.dumps({
                "questions": context.get("questions", []),
                "answers": [a.get("answer", "") for a in context.get("answers", [])],
                "evaluations": context.get("evaluations", []),
                "stage": stage
            }),
            base_question=context.get("questions", [])[-1] if context.get("questions") else "",
            sample_answer=context.get("sample_answers", [])[-1] if context.get("sample_answers") else "",
            session_id=session_id
        )
    except Exception as e:
        print(f"Error in generate_followup: {str(e)}")
        question_text = ""

    # If generate_followup returned None or blank, end interview
    if not question_text or question_text.strip() == "":
        return jsonify({"done": True, "message": "No more questions available"}), 200

    # Generate question ID
    question_id = hashlib.md5(question_text.encode()).hexdigest()

    # Append to context
    context["stage"] = stage
    context["question_count"] = q_count + 1
    context["topics"].append(topic)
    context["questions"].append(question_text)
    context["sample_answers"].append(sample_answer or "")
    _save_context(user_id, session_id, context)

    # Generate TTS
    try:
        audio_bytes = get_tts(question_id, question_text)
    except Exception as e:
        print(f"Error in get_tts: {str(e)}")
        return jsonify({"error": "Failed to generate audio"}), 500

    return jsonify({
        "question_id": question_id,
        "question": question_text,
        "audio": audio_bytes.hex(),
        "sample_answer": sample_answer,
        "stage": stage
    })


# ===== Submit Answer =====
@interview_bp.route("/answer", methods=["POST"])
@jwt_required()
def submit_answer():
    """Store answer without evaluation (batch eval at end)."""
    user_id = int(get_jwt_identity())
    session_id = request.form.get("session_id")

    question_id = request.form.get("question_id")
    sample_answer = request.form.get("sample_answer", "")
    audio_file = request.files.get("audio")

    if not session_id or not question_id or not audio_file:
        return jsonify({"error": "session_id, question_id, and audio are required"}), 400

    context = _load_context(user_id, session_id)

    try:
        transcript = transcribe_audio(audio_file.read())
    except Exception as e:
        print(f"Error in transcribe_audio: {str(e)}")
        return jsonify({"error": "Failed to transcribe audio"}), 500

    if not transcript:
        return jsonify({"error": "Failed to transcribe audio: empty transcript"}), 500

    flagged = is_scripted_answer(transcript, sample_answer)

        # === Pre-question evaluation (immediate) ===
    try:
        stage = context["stage"] if "stage" in context else "intro"
        eval_result = generate_evaluation(
            question=context["questions"][-1],
            candidate_answer=transcript,
            sample_answer=sample_answer,
            stage=stage,
            resume_text=User.query.get(user_id).resume_text or ""
        )

        # Save evaluation into context
        context.setdefault("evaluations", []).append(eval_result)
        _save_context(user_id, session_id, context)

        # Cache evaluation separately in Redis
        cache_key = f"evaluation:{user_id}:{session_id}:{question_id}"
        r.setex(cache_key, 86400, json.dumps(eval_result, ensure_ascii=False))
    except Exception as e:
        print(f"Error in pre-question evaluation: {e}")

    # Append answer
    context.setdefault("answers", []).append({
        "question_id": question_id,
        "answer": transcript,
        "flagged": flagged
    })
    _save_context(user_id, session_id, context)

    # Save raw answer to DB
    q = InterviewQuestion(
        session_id=session_id,
        question=context["questions"][-1] if context["questions"] else "",
        answer=transcript,
        score=None,
        flagged_script=flagged
    )
    db.session.add(q)
    db.session.commit()

    return jsonify({
        "transcript": transcript,
        "flagged_script": flagged
    })




# ===== Summary =====
@interview_bp.route("/summary", methods=["POST"])
@jwt_required()
def get_summary():
    """Batch evaluate all answers using actual data and return final summary."""
    data = request.get_json()
    session_id = data.get("session_id")
    user_id = int(get_jwt_identity())

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    context = _load_context(user_id, session_id)
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    resume_text = getattr(user, "resume_text", "")

    # Limit to 5 questions
    questions_limited = context.get("questions", [])[:5]
    sample_answers_limited = context.get("sample_answers", [])[:5]
    answers = context.get("answers", [])[:5]

    # Pad missing answers
    while len(answers) < len(questions_limited):
        answers.append({"answer": "", "flagged": False})

    context["questions"] = questions_limited
    context["sample_answers"] = sample_answers_limited
    context["answers"] = answers

    # Build Q/A pairs
    qa_pairs = []
    for idx, (question, ans_obj) in enumerate(zip(questions_limited, answers)):
        if idx == 0:
            stage = "intro"
        elif idx in (1, 2):
            stage = "resume"
        elif idx == 3:
            stage = "technical"
        else:
            stage = "hr"

        qa_pairs.append({
            "question": question,
            "answer": ans_obj.get("answer", ""),
            "sample_answer": sample_answers_limited[idx] if idx < len(sample_answers_limited) else "",
            "stage": stage,
            "resume_context": resume_text
        })

        # Load all pre-stored evaluations from Redis
    eval_keys = r.keys(f"evaluation:{user_id}:{session_id}:*")
    evaluations = []
    for k in eval_keys:
        try:
            evaluations.append(json.loads(r.get(k)))
        except Exception as e:
            print(f"Error reading cached evaluation: {e}")

    # Ensure order matches question list
    if len(evaluations) < len(questions_limited):
        evaluations += [default_eval.copy()] * (len(questions_limited) - len(evaluations))

    # Ensure all evaluations have a question context
    for i, eval in enumerate(evaluations):
        if "question" not in eval:
            eval["question"] = questions_limited[i] if i < len(questions_limited) else ""

    # Ensure length and defaults
    default_eval = {
        "question": "",
        "answer": "",
        "technical_score": None,
        "completeness_score": None,
        "communication_score": None,
        "depth_of_knowledge": None,
        "problem_solving_score": None,
        "verdict": None,
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
        "summary": ""
    }
    while len(evaluations) < len(questions_limited):
        evaluations.append(default_eval.copy())

    # Save in context
    context["evaluations"] = evaluations
    _save_context(user_id, session_id, context)

    # Generate final summary
    summary_data = generate_summary(questions=questions_limited, evaluations=evaluations)

    # Trim summary length to 21–25 words
    if isinstance(summary_data.get("summary"), str):
        words = summary_data["summary"].split()
        if len(words) > 25:
            summary_data["summary"] = " ".join(words[:25])
        elif len(words) < 21 and words:
            summary_data["summary"] += " " + " ".join([words[-1]] * (21 - len(words)))

    context["final_summary"] = summary_data
    _save_context(user_id, session_id, context)

    cleanup_session_cache(user_id, session_id, keep_fields=["evaluations", "final_summary"])

    return jsonify({
        "evaluations": evaluations,
        "summary": summary_data
    })


# ===== Resume Upload =====
@interview_bp.route("/upload_resume", methods=["POST"])
@jwt_required()
def upload_resume():
    user_id = int(get_jwt_identity())
    file = request.files.get("resume")

    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a valid PDF resume"}), 400

    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    except Exception as e:
        print(f"Error in resume parsing: {str(e)}")
        return jsonify({"error": "Failed to parse PDF resume"}), 500

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.resume_text = text
    db.session.commit()

    try:
        build_resume_index(user_id, text)
    except Exception as e:
        print(f"Error in build_resume_index: {str(e)}")
        return jsonify({"error": "Failed to index resume"}), 500

    return jsonify({"message": "Resume uploaded, parsed, and indexed successfully"})