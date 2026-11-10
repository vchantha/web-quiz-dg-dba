from django.conf import settings
from django.db import models

class Quiz(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    pass_percent = models.PositiveSmallIntegerField(default=76)
    published = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Question(models.Model):
    DBA = "DBA"
    GOVERNANCE = "Data Governance"
    DOMAIN_CHOICES = [(DBA, DBA), (GOVERNANCE, GOVERNANCE)]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    position = models.PositiveSmallIntegerField()
    domain = models.CharField(max_length=32, choices=DOMAIN_CHOICES)
    topic = models.CharField(max_length=120)
    difficulty = models.CharField(max_length=30, default="Intermediate")
    text = models.TextField()
    correct_code = models.CharField(max_length=1)
    explanation = models.TextField()
    points = models.PositiveSmallIntegerField(default=4)
    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["quiz", "position"], name="unique_quiz_position")]
    def __str__(self):
        return f"{self.position}. {self.text[:60]}"

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    code = models.CharField(max_length=1)
    text = models.TextField()
    class Meta:
        ordering = ["code"]
        constraints = [models.UniqueConstraint(fields=["question", "code"], name="unique_question_code")]

class Attempt(models.Model):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"
    STATUS_CHOICES = [(IN_PROGRESS, "In progress"), (SUBMITTED, "Submitted"), (EXPIRED, "Expired")]
    quiz = models.ForeignKey(Quiz, on_delete=models.PROTECT, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quiz_attempts")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=IN_PROGRESS)
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    question_snapshot = models.JSONField(default=list)
    correct_count = models.PositiveSmallIntegerField(default=0)
    score = models.PositiveSmallIntegerField(default=0)
    possible_score = models.PositiveSmallIntegerField(default=100)
    class Meta:
        indexes = [models.Index(fields=["user", "quiz", "status"], name="attempt_user_quiz_idx")]
        ordering = ["-started_at"]

class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question_id_snapshot = models.PositiveIntegerField()
    selected_code = models.CharField(max_length=1)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["attempt", "question_id_snapshot"], name="unique_attempt_answer")]

class AuditEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    attempt = models.ForeignKey(Attempt, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
