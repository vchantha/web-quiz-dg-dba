from django.urls import path
from . import views
urlpatterns = [
    path("health", views.health),
    path("auth/session", views.session),
    path("auth/login", views.sign_in),
    path("auth/logout", views.sign_out),
    path("assessments", views.assessments),
    path("attempts", views.start_attempt),
    path("attempts/current", views.current_attempt),
    path("attempts/<int:attempt_id>", views.get_attempt),
    path("attempts/<int:attempt_id>/answers/<int:question_id>", views.save_answer),
    path("attempts/<int:attempt_id>/submit", views.submit_attempt),
    path("results/<int:attempt_id>", views.result),
    path("admin/summary", views.admin_summary),
    path("admin/results.csv", views.admin_export),
]
