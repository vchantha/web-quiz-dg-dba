from django.contrib import admin
from .models import Answer, Attempt, AuditEvent, Option, Question, Quiz

class OptionInline(admin.TabularInline):
    model = Option
    extra = 0

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "duration_minutes", "pass_percent", "published", "version")
    list_filter = ("published",)
    search_fields = ("title", "slug")

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("position", "quiz", "domain", "topic", "points")
    list_filter = ("quiz", "domain", "difficulty")
    search_fields = ("text", "topic")
    inlines = [OptionInline]

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "status", "score", "possible_score", "started_at", "submitted_at")
    list_filter = ("quiz", "status")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "quiz", "status", "started_at", "expires_at", "submitted_at", "question_snapshot", "correct_count", "score", "possible_score")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question_id_snapshot", "selected_code", "updated_at")
    readonly_fields = ("attempt", "question_id_snapshot", "selected_code", "updated_at")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(AuditEvent)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "event", "user", "attempt")
    readonly_fields = ("created_at", "user", "attempt", "event", "metadata")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
