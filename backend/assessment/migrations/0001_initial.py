# Generated for the DBA & Data Governance assessment data model.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Quiz", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("slug", models.SlugField(max_length=100, unique=True)),
            ("title", models.CharField(max_length=240)),
            ("description", models.TextField(blank=True)),
            ("duration_minutes", models.PositiveSmallIntegerField(default=60)),
            ("pass_percent", models.PositiveSmallIntegerField(default=76)),
            ("published", models.BooleanField(default=True)),
            ("version", models.PositiveIntegerField(default=1)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="Question", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("position", models.PositiveSmallIntegerField()),
            ("domain", models.CharField(choices=[("DBA", "DBA"), ("Data Governance", "Data Governance")], max_length=32)),
            ("topic", models.CharField(max_length=120)),
            ("difficulty", models.CharField(default="Intermediate", max_length=30)),
            ("text", models.TextField()),
            ("correct_code", models.CharField(max_length=1)),
            ("explanation", models.TextField()),
            ("points", models.PositiveSmallIntegerField(default=4)),
            ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="assessment.quiz")),
        ], options={"ordering": ["position"]}),
        migrations.CreateModel(name="Option", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("code", models.CharField(max_length=1)),
            ("text", models.TextField()),
            ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="assessment.question")),
        ], options={"ordering": ["code"]}),
        migrations.CreateModel(name="Attempt", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("status", models.CharField(choices=[("in_progress", "In progress"), ("submitted", "Submitted"), ("expired", "Expired")], default="in_progress", max_length=20)),
            ("started_at", models.DateTimeField()),
            ("expires_at", models.DateTimeField()),
            ("submitted_at", models.DateTimeField(blank=True, null=True)),
            ("question_snapshot", models.JSONField(default=list)),
            ("correct_count", models.PositiveSmallIntegerField(default=0)),
            ("score", models.PositiveSmallIntegerField(default=0)),
            ("possible_score", models.PositiveSmallIntegerField(default=100)),
            ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attempts", to="assessment.quiz")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="quiz_attempts", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-started_at"]}),
        migrations.CreateModel(name="Answer", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("question_id_snapshot", models.PositiveIntegerField()),
            ("selected_code", models.CharField(max_length=1)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="assessment.attempt")),
        ]),
        migrations.CreateModel(name="AuditEvent", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("event", models.CharField(max_length=50)),
            ("metadata", models.JSONField(blank=True, default=dict)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("attempt", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="assessment.attempt")),
            ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-created_at"]}),
        migrations.AddConstraint(model_name="question", constraint=models.UniqueConstraint(fields=("quiz", "position"), name="unique_quiz_position")),
        migrations.AddConstraint(model_name="option", constraint=models.UniqueConstraint(fields=("question", "code"), name="unique_question_code")),
        migrations.AddConstraint(model_name="answer", constraint=models.UniqueConstraint(fields=("attempt", "question_id_snapshot"), name="unique_attempt_answer")),
        migrations.AddIndex(model_name="attempt", index=models.Index(fields=["user", "quiz", "status"], name="attempt_user_quiz_idx")),
    ]
