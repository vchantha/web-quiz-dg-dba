"""JSON endpoints for candidate assessment and staff reporting.

Never send answer keys before submission. Exam deadlines and scoring live on the server.
"""
import csv
import json
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import Answer, Attempt, AuditEvent, Quiz


def failure(message, status=400):
    return JsonResponse({"error": message}, status=status)


def parse_body(request):
    try:
        value = json.loads(request.body or b"{}")
        return value if isinstance(value, dict) else {}
    except (ValueError, UnicodeError):
        return {}


def authenticated(view):
    @wraps(view)
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return failure("Please sign in to continue.", 401)
        return view(request, *args, **kwargs)
    return inner


def staff_only(view):
    @wraps(view)
    @authenticated
    def inner(request, *args, **kwargs):
        if not request.user.is_staff:
            return failure("Staff permission required.", 403)
        return view(request, *args, **kwargs)
    return inner


def log_event(user, event, attempt=None, metadata=None):
    AuditEvent.objects.create(user=user, attempt=attempt, event=event, metadata=metadata or {})


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
@ensure_csrf_cookie
def session(request):
    user = request.user
    return JsonResponse({"authenticated": user.is_authenticated, "user": {
        "id": user.pk, "username": user.username, "name": user.get_full_name() or user.username,
        "is_staff": user.is_staff,
    } if user.is_authenticated else None})


@require_POST
def sign_in(request):
    data = parse_body(request)
    username = str(data.get("username", "")).strip()
    password = data.get("password", "")
    if not username or not isinstance(password, str):
        return failure("Username and password are required.")
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        return failure("Invalid username or password.", 401)
    login(request, user)
    log_event(user, "login")
    return JsonResponse({"authenticated": True, "user": {
        "id": user.pk, "username": user.username,
        "name": user.get_full_name() or user.username, "is_staff": user.is_staff,
    }})


@require_POST
@authenticated
def sign_out(request):
    log_event(request.user, "logout")
    logout(request)
    return JsonResponse({"ok": True})


def quiz_summary(quiz):
    questions = list(quiz.questions.all())
    return {
        "id": quiz.id, "slug": quiz.slug, "title": quiz.title,
        "description": quiz.description, "duration_minutes": quiz.duration_minutes,
        "pass_percent": quiz.pass_percent,
        "question_count": len(questions),
        "possible_score": sum(q.points for q in questions),
        "domains": [
            {"name": label, "questions": sum(1 for q in questions if q.domain == label),
             "points": sum(q.points for q in questions if q.domain == label)}
            for label in ("DBA", "Data Governance")
        ],
    }


@require_GET
@authenticated
def assessments(request):
    quiz = Quiz.objects.filter(published=True).prefetch_related("questions").first()
    if not quiz:
        return failure("No published assessment is available.", 404)
    return JsonResponse({"assessment": quiz_summary(quiz), "max_attempts": settings.QUIZ_MAX_ATTEMPTS})


def snapshot_question(q):
    return {
        "id": q.id, "number": q.position, "domain": q.domain,
        "topic": q.topic, "difficulty": q.difficulty, "text": q.text,
        "points": q.points, "correct_code": q.correct_code,
        "explanation": q.explanation,
        "options": [{"code": o.code, "text": o.text} for o in q.options.all()],
    }


def public_question(q):
    return {key: value for key, value in q.items() if key not in ("correct_code", "explanation")}


def expire_if_due(attempt):
    if attempt.status == Attempt.IN_PROGRESS and timezone.now() >= attempt.expires_at:
        finalize_locked(attempt, expired=True)
    return attempt.status != Attempt.IN_PROGRESS


def finalize_locked(attempt, expired=False):
    """Caller holds a SELECT FOR UPDATE row lock on this attempt."""
    if attempt.status != Attempt.IN_PROGRESS:
        return
    answers = dict(attempt.answers.values_list("question_id_snapshot", "selected_code"))
    snapshot = attempt.question_snapshot
    attempt.correct_count = sum(
        answers.get(q["id"]) == q["correct_code"] for q in snapshot
    )
    attempt.score = sum(
        q["points"] for q in snapshot
        if answers.get(q["id"]) == q["correct_code"]
    )
    attempt.possible_score = sum(q["points"] for q in snapshot)
    attempt.status = Attempt.EXPIRED if expired else Attempt.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.save(update_fields=[
        "correct_count", "score", "possible_score", "status", "submitted_at"
    ])
    log_event(attempt.user, "attempt_finalized", attempt, {
        "status": attempt.status, "score": attempt.score
    })


def serialize_attempt(attempt):
    answers = {str(qid): code for qid, code in attempt.answers.values_list(
        "question_id_snapshot", "selected_code"
    )}
    return {
        "id": attempt.id, "status": attempt.status, "started_at": attempt.started_at.isoformat(),
        "expires_at": attempt.expires_at.isoformat(), "remaining_seconds": max(
            0, int((attempt.expires_at - timezone.now()).total_seconds())
        ),
        "questions": [public_question(q) for q in attempt.question_snapshot],
        "answers": answers, "answered_count": len(answers),
    }


def find_owned_attempt(request, attempt_id, lock=False):
    queryset = Attempt.objects.select_for_update() if lock else Attempt.objects.all()
    if not request.user.is_staff:
        queryset = queryset.filter(user=request.user)
    return queryset.filter(pk=attempt_id).first()


@require_POST
@authenticated
def start_attempt(request):
    with transaction.atomic():
        # Lock the user so two concurrent start requests cannot create extra attempts.
        User.objects.select_for_update().get(pk=request.user.pk)
        quiz = Quiz.objects.filter(published=True).first()
        if not quiz:
            return failure("No published assessment.", 404)
        previous = list(Attempt.objects.filter(user=request.user, quiz=quiz).order_by("-started_at"))
        for attempt in previous:
            if attempt.status == Attempt.IN_PROGRESS:
                attempt = Attempt.objects.select_for_update().get(pk=attempt.pk)
                if not expire_if_due(attempt):
                    return JsonResponse({"attempt": serialize_attempt(attempt), "resumed": True})
        if len(previous) >= settings.QUIZ_MAX_ATTEMPTS:
            return failure("Attempt limit reached. Contact the assessor for another attempt.", 409)
        questions = list(quiz.questions.prefetch_related("options").order_by("position"))
        if not questions or any(q.options.count() != 4 for q in questions):
            return failure("The assessment is not configured correctly.", 503)
        now = timezone.now()
        attempt = Attempt.objects.create(
            user=request.user, quiz=quiz, started_at=now,
            expires_at=now + timedelta(minutes=quiz.duration_minutes),
            question_snapshot=[snapshot_question(q) for q in questions],
            possible_score=sum(q.points for q in questions),
        )
        log_event(request.user, "attempt_started", attempt, {"quiz_version": quiz.version})
        return JsonResponse({"attempt": serialize_attempt(attempt), "resumed": False}, status=201)


@require_GET
@authenticated
def current_attempt(request):
    quiz = Quiz.objects.filter(published=True).first()
    attempt = Attempt.objects.filter(user=request.user, quiz=quiz).first() if quiz else None
    if not attempt:
        return JsonResponse({"attempt": None})
    with transaction.atomic():
        attempt = Attempt.objects.select_for_update().get(pk=attempt.id)
        expire_if_due(attempt)
        if attempt.status != Attempt.IN_PROGRESS:
            return JsonResponse({"attempt": None, "result_id": attempt.id, "status": attempt.status})
        return JsonResponse({"attempt": serialize_attempt(attempt)})


@require_GET
@authenticated
def get_attempt(request, attempt_id):
    with transaction.atomic():
        attempt = find_owned_attempt(request, attempt_id, lock=True)
        if attempt is None:
            return failure("Attempt not found.", 404)
        if expire_if_due(attempt):
            return JsonResponse({"attempt": None, "result_id": attempt.id, "status": attempt.status})
        return JsonResponse({"attempt": serialize_attempt(attempt)})


@require_http_methods(["PUT"])
@authenticated
def save_answer(request, attempt_id, question_id):
    data = parse_body(request)
    selected = data.get("selected_code")
    if not isinstance(selected, str) or selected not in ("A", "B", "C", "D"):
        return failure("Select one valid option: A, B, C, or D.")
    with transaction.atomic():
        attempt = Attempt.objects.select_for_update().filter(
            pk=attempt_id, user=request.user
        ).first()
        if attempt is None:
            return failure("Attempt not found.", 404)
        if expire_if_due(attempt):
            return failure("This attempt has finished; answers are locked.", 409)
        question = next((q for q in attempt.question_snapshot if q["id"] == question_id), None)
        if not question or selected not in [o["code"] for o in question["options"]]:
            return failure("This question or option does not belong to the attempt.", 400)
        Answer.objects.update_or_create(
            attempt=attempt, question_id_snapshot=question_id,
            defaults={"selected_code": selected}
        )
        return JsonResponse({
            "saved": True, "answered_count": attempt.answers.count(),
            "question_id": question_id, "selected_code": selected,
        })


@require_POST
@authenticated
def submit_attempt(request, attempt_id):
    with transaction.atomic():
        attempt = Attempt.objects.select_for_update().filter(
            pk=attempt_id, user=request.user
        ).first()
        if attempt is None:
            return failure("Attempt not found.", 404)
        if attempt.status == Attempt.IN_PROGRESS:
            finalize_locked(attempt, expired=timezone.now() >= attempt.expires_at)
        return JsonResponse({"result_id": attempt.id, "status": attempt.status})


@require_GET
@authenticated
def result(request, attempt_id):
    with transaction.atomic():
        attempt = find_owned_attempt(request, attempt_id, lock=True)
        if attempt is None:
            return failure("Result not found.", 404)
        if not expire_if_due(attempt):
            return failure("The assessment has not finished.", 409)
        answers = dict(attempt.answers.values_list("question_id_snapshot", "selected_code"))
        topics = {}
        domains = {}
        review = []
        for q in attempt.question_snapshot:
            correct = answers.get(q["id"]) == q["correct_code"]
            for key, bucket in ((q["topic"], topics), (q["domain"], domains)):
                row = bucket.setdefault(key, {"name": key, "questions": 0, "correct": 0, "score": 0, "possible": 0})
                row["questions"] += 1
                row["correct"] += int(correct)
                row["score"] += q["points"] if correct else 0
                row["possible"] += q["points"]
            if settings.QUIZ_SHOW_ANSWER_REVIEW or request.user.is_staff:
                review.append({
                    **public_question(q), "selected_code": answers.get(q["id"]),
                    "correct_code": q["correct_code"], "explanation": q["explanation"],
                })
        return JsonResponse({
            "id": attempt.id, "status": attempt.status,
            "quiz_title": attempt.quiz.title, "candidate_name": attempt.user.get_full_name() or attempt.user.username,
            "score": attempt.score, "possible_score": attempt.possible_score,
            "percent": round(attempt.score * 100 / max(attempt.possible_score, 1)),
            "passed": attempt.score * 100 >= attempt.quiz.pass_percent * attempt.possible_score,
            "pass_percent": attempt.quiz.pass_percent, "correct_count": attempt.correct_count,
            "total_questions": len(attempt.question_snapshot),
            "answered_count": len(answers),
            "time_taken_seconds": int((attempt.submitted_at - attempt.started_at).total_seconds()),
            "submitted_at": attempt.submitted_at.isoformat(),
            "domains": list(domains.values()), "topics": list(topics.values()),
            "review_available": bool(review), "review": review,
        })


@require_GET
@staff_only
def admin_summary(request):
    attempts = list(Attempt.objects.select_related("user", "quiz").order_by("-started_at")[:200])
    complete = [a for a in attempts if a.status != Attempt.IN_PROGRESS]
    return JsonResponse({
        "total_candidates": User.objects.filter(is_staff=False, is_active=True).count(),
        "total_attempts": Attempt.objects.count(),
        "completed_attempts": Attempt.objects.exclude(status=Attempt.IN_PROGRESS).count(),
        "average_score": round(sum(a.score * 100 / max(a.possible_score, 1) for a in complete) / len(complete), 1) if complete else 0,
        "attempts": [{
            "id": a.id, "candidate": a.user.get_full_name() or a.user.username,
            "username": a.user.username, "status": a.status,
            "score": a.score, "possible": a.possible_score,
            "started_at": a.started_at.isoformat(),
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        } for a in attempts],
    })


@require_GET
@staff_only
def admin_export(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="assessment-results.csv"'
    writer = csv.writer(response)
    writer.writerow(["Candidate", "Username", "Status", "Score", "Possible", "Started at", "Submitted at"])
    for a in Attempt.objects.select_related("user").order_by("-started_at").iterator():
        writer.writerow([
            a.user.get_full_name() or a.user.username, a.user.username, a.status,
            a.score, a.possible_score, a.started_at.isoformat(),
            a.submitted_at.isoformat() if a.submitted_at else "",
        ])
    log_event(request.user, "results_exported")
    return response
