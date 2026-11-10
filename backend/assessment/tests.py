"""Integration tests for timed exams, role separation, scoring and persistence."""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import Answer, Attempt, Question, Quiz

User = get_user_model()

class AssessmentApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_quiz", verbosity=0)
        cls.quiz = Quiz.objects.get(slug="dba-governance-25")
        cls.candidate = User.objects.create_user(username="candidate1", password="candidate-pass-long")
        cls.other = User.objects.create_user(username="candidate2", password="candidate-pass-long")
        cls.assessor = User.objects.create_user(username="assessor1", password="assessor-pass-long", is_staff=True)

    def setUp(self):
        self.client.force_login(self.candidate)

    def start(self):
        response = self.client.post("/api/attempts")
        self.assertEqual(response.status_code, 201)
        return response.json()["attempt"]

    def answer(self, attempt_id, question_id, code):
        return self.client.put(
            f"/api/attempts/{attempt_id}/answers/{question_id}",
            data=json.dumps({"selected_code": code}), content_type="application/json",
        )

    def test_question_bank_and_scoring_weights(self):
        self.assertEqual(Question.objects.filter(quiz=self.quiz).count(), 25)
        self.assertEqual(Question.objects.filter(quiz=self.quiz, domain="DBA").count(), 13)
        self.assertEqual(Question.objects.filter(quiz=self.quiz, domain="Data Governance").count(), 12)
        self.assertEqual(sum(Question.objects.values_list("points", flat=True)), 100)
        self.assertEqual(self.quiz.duration_minutes, 60)

    def test_attempt_quota_metadata_changes_after_start(self):
        before = self.client.get("/api/assessments").json()
        self.assertEqual(before["max_attempts"], 1)
        self.assertEqual(before["attempts_used"], 0)
        self.start()
        after = self.client.get("/api/assessments").json()
        self.assertEqual(after["attempts_used"], 1)

    def test_seed_is_idempotent(self):
        call_command("seed_quiz", verbosity=0)
        self.assertEqual(self.quiz.questions.count(), 25)
        self.assertEqual(sum(q.options.count() for q in self.quiz.questions.all()), 100)

    def test_public_questions_never_leak_correct_answer(self):
        attempt = self.start()
        self.assertEqual(len(attempt["questions"]), 25)
        self.assertNotIn("correct_code", attempt["questions"][0])
        self.assertNotIn("explanation", attempt["questions"][0])
        self.assertEqual(len(attempt["questions"][0]["options"]), 4)
        self.assertGreaterEqual(attempt["remaining_seconds"], 3598)
        self.assertLessEqual(attempt["remaining_seconds"], 3600)

    def test_autosave_and_resume_are_persistent(self):
        attempt = self.start()
        first = attempt["questions"][0]
        saved = self.answer(attempt["id"], first["id"], "A")
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["answered_count"], 1)
        self.assertEqual(Answer.objects.count(), 1)
        resumed = self.client.get("/api/attempts/current").json()["attempt"]
        self.assertEqual(resumed["answers"][str(first["id"])], "A")
        same = self.client.post("/api/attempts")
        self.assertEqual(same.status_code, 200)
        self.assertTrue(same.json()["resumed"])
        self.assertEqual(same.json()["attempt"]["id"], attempt["id"])

    def test_full_marks_submit_is_idempotent_and_locks_answers(self):
        attempt = self.start()
        for question in self.quiz.questions.all():
            saved = self.answer(attempt["id"], question.id, question.correct_code)
            self.assertEqual(saved.status_code, 200)
        submitted = self.client.post(f"/api/attempts/{attempt['id']}/submit")
        self.assertEqual(submitted.status_code, 200)
        submitted_again = self.client.post(f"/api/attempts/{attempt['id']}/submit")
        self.assertEqual(submitted_again.status_code, 200)
        result = self.client.get(f"/api/results/{attempt['id']}").json()
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["correct_count"], 25)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["domains"]), 2)
        self.assertFalse(result["review_available"])
        self.assertEqual(self.answer(attempt["id"], attempt["questions"][0]["id"], "A").status_code, 409)

    def test_timeout_scores_existing_answers_and_rejects_future_saves(self):
        attempt = self.start()
        row = Attempt.objects.get(pk=attempt["id"])
        row.expires_at = timezone.now() - timedelta(seconds=1)
        row.save(update_fields=["expires_at"])
        response = self.answer(attempt["id"], attempt["questions"][0]["id"], "B")
        self.assertEqual(response.status_code, 409)
        row.refresh_from_db()
        self.assertEqual(row.status, Attempt.EXPIRED)
        self.assertEqual(row.score, 0)

    def test_candidate_cannot_access_other_candidate_attempt(self):
        attempt = self.start()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f"/api/attempts/{attempt['id']}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/results/{attempt['id']}").status_code, 404)
        self.assertEqual(self.answer(attempt["id"], attempt["questions"][0]["id"], "A").status_code, 404)

    def test_retake_disabled_without_assessor_authorization(self):
        attempt = self.start()
        self.client.post(f"/api/attempts/{attempt['id']}/submit")
        self.assertEqual(self.client.post("/api/attempts").status_code, 409)

    def test_staff_only_reporting(self):
        self.assertEqual(self.client.get("/api/admin/summary").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/results.csv").status_code, 403)
        self.client.force_login(self.assessor)
        self.assertEqual(self.client.get("/api/admin/summary").status_code, 200)
        export = self.client.get("/api/admin/results.csv")
        self.assertEqual(export.status_code, 200)
        self.assertEqual(export["Content-Type"], "text/csv")

    def test_unauthenticated_api_is_unauthorized(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/assessments").status_code, 401)
        self.assertEqual(self.client.post("/api/attempts").status_code, 401)
