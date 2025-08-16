from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from prisma import Prisma
from utils.faiss_index import search_questions, search_resume, build_resume_index
from utils.tts import get_tts
from utils.stt import transcribe_audio
from utils.llm import generate_followup, generate_summary, generate_evaluation, _call_gemini, key_rotator
from utils.cache import r, is_scripted_answer, cleanup_session_cache
import json
import hashlib
import pdfplumber
import asyncio

interview_bp = Blueprint("interview", __name__)
prisma = Prisma()

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
    if q_count == 1:
        return "intro"
    elif 2 <= q_count <= 3:
        return "resume"
    elif q_count == 4:
        return "technical"
    else:
        return "closing"


# ===== Start Interview =====
@interview_bp.route("/start", methods=["POST"])
@jwt_required()
def start_interview():
    user_id = int(get_jwt_identity())

    async def _start():
        await prisma.connect()
        session = await prisma.interviewsession.create(
            data={
                "userId": user_id,
            }
        )
        await prisma.disconnect()

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

    return asyncio.run(_start())


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

    context = _load_context(user_id, session_id)
    q_count = context.get("question_count", 0)

    if q_count >= 5:
        return jsonify({"done": True, "message": "Interview completed"}), 200

    stage = _get_stage(q_count)
    question_text = ""
    sample_answer = ""

    try:
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

    if not question_text or question_text.strip() == "":
        return jsonify({"done": True, "message": "No more questions available"}), 200

    question_id = hashlib.md5(question_text.encode()).hexdigest()

    context["stage"] = stage
    context["question_count"] = q_count + 1
    context["topics"].append(topic)
    context["questions"].append(question_text)
    context["sample_answers"].append(sample_answer or "")
    _save_context(user_id, session_id, context)

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

    try:
        stage = context["stage"] if "stage" in context else "intro"
        async def _eval_and_save():
            await prisma.connect()
            user = await prisma.user.find_unique(where={"id": user_id})
            resume_text = user.resumeText if user else ""

            eval_result = generate_evaluation(
                question=context["questions"][-1],
                candidate_answer=transcript,
                sample_answer=sample_answer,
                stage=stage,
                resume_text=resume_text
            )

            context.setdefault("evaluations", []).append(eval_result)
            _save_context(user_id, session_id, context)

            cache_key = f"evaluation:{user_id}:{session_id}:{question_id}"
            r.setex(cache_key, 86400, json.dumps(eval_result, ensure_ascii=False))

            # Save raw answer to DB
            await prisma.interviewquestion.create(
                data={
                    "sessionId": int(session_id),
                    "question": context["questions"][-1] if context["questions"] else "",
                    "answer": transcript,
                    "score": None,
                    "flaggedScript": flagged,
                }
            )

            await prisma.disconnect()

        asyncio.run(_eval_and_save())

    except Exception as e:
        print(f"Error in pre-question evaluation: {e}")

    context.setdefault("answers", []).append({
        "question_id": question_id,
        "answer": transcript,
        "flagged": flagged
    })
    _save_context(user_id, session_id, context)

    return jsonify({
        "transcript": transcript,
        "flagged_script": flagged
    })


# ===== Summary =====
@interview_bp.route("/summary", methods=["POST"])
@jwt_required()
def get_summary():
    data = request.get_json()
    session_id = data.get("session_id")
    user_id = int(get_jwt_identity())

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    context = _load_context(user_id, session_id)

    async def _fetch_user_resume():
        await prisma.connect()
        user = await prisma.user.find_unique(where={"id": user_id})
        await prisma.disconnect()
        return user.resumeText if user else ""

    resume_text = asyncio.run(_fetch_user_resume())

    questions_limited = context.get("questions", [])[:5]
    sample_answers_limited = context.get("sample_answers", [])[:5]
    answers = context.get("answers", [])[:5]

    while len(answers) < len(questions_limited):
        answers.append({"answer": "", "flagged": False})

    context["questions"] = questions_limited
    context["sample_answers"] = sample_answers_limited
    context["answers"] = answers

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

    eval_keys = r.keys(f"evaluation:{user_id}:{session_id}:*")
    evaluations = []
    for k in eval_keys:
        try:
            evaluations.append(json.loads(r.get(k)))
        except Exception as e:
            print(f"Error reading cached evaluation: {e}")

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

    for i, eval in enumerate(evaluations):
        if "question" not in eval:
            eval["question"] = questions_limited[i] if i < len(questions_limited) else ""

    context["evaluations"] = evaluations
    _save_context(user_id, session_id, context)

    summary_data = generate_summary(questions=questions_limited, evaluations=evaluations)

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

    async def _save_resume():
        await prisma.connect()
        await prisma.user.update(
            where={"id": user_id},
            data={"resumeText": text}
        )
        await prisma.disconnect()

    asyncio.run(_save_resume())

    try:
        build_resume_index(user_id, text)
    except Exception as e:
        print(f"Error in build_resume_index: {str(e)}")
        return jsonify({"error": "Failed to index resume"}), 500

    return jsonify({"message": "Resume uploaded, parsed, and indexed successfully"})
