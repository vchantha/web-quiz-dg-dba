"""Idempotently seed the published 25-question assessment. No demo users by default."""
import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from assessment.models import Option, Question, Quiz
from assessment.question_bank import get_bank

class Command(BaseCommand):
    help = "Seed the 25-question DBA + Data Governance assessment without overwriting edits."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        bank = get_bank()
        quiz, _ = Quiz.objects.get_or_create(
            slug="dba-governance-25",
            defaults={
                "title": "DBA & Data Governance Assessment",
                "description": "Demonstrate practical database administration and data governance knowledge.",
                "duration_minutes": 60, "pass_percent": 76,
            }
        )
        created = 0
        for row in bank:
            q, is_new = Question.objects.get_or_create(
                quiz=quiz, position=row["position"],
                defaults={key: row[key] for key in (
                    "domain", "topic", "difficulty", "text", "correct_code", "explanation"
                )} | {"points": 4},
            )
            created += int(is_new)
            for code, value in row["options"].items():
                Option.objects.get_or_create(question=q, code=code, defaults={"text": value})
        if os.environ.get("SEED_DEMO_USERS") == "1":
            User = get_user_model()
            for username, password_key, is_staff in (
                ("candidate", "DEMO_CANDIDATE_PASSWORD", False),
                ("assessor", "DEMO_ADMIN_PASSWORD", True),
            ):
                password = os.environ.get(password_key)
                if not password or len(password) < 10:
                    raise CommandError(f"{password_key} must be at least 10 characters when SEED_DEMO_USERS=1")
                if not User.objects.filter(username=username).exists():
                    User.objects.create_user(
                        username=username, password=password,
                        is_staff=is_staff, is_superuser=is_staff,
                    )
        self.stdout.write(self.style.SUCCESS(
            f"Quiz ready: {len(bank)} questions (new: {created}); 13 DBA, 12 Governance, 100 points."
        ))
