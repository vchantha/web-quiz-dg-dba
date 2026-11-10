# DBA & Data Governance — Online Assessment Platform

A full-stack, responsive recruitment quiz application: **Login → Overview → Instructions → 25-question Assessment → My Result**. An assessor dashboard and Django Admin manage users, the question bank and reporting.

## Screens and capabilities

- **Login:** Django session authentication, CSRF protection, role-aware navigation.
- **Overview:** 25 questions, 100 points, 60 minutes; DBA 13 questions (52 points) and Data Governance 12 (48 points).
- **Instructions:** Exam rules, categories, scoring and time limit.
- **Assessment:** One answer per question, 25-step navigator, server-backed autosave, refresh/resume, server-enforced deadline, automatic timeout handling and final confirmation.
- **Results:** Pass/fail, overall score, DBA vs Governance breakdown, topic analysis and print/save-as-PDF.
- **Staff:** Authorized candidate summary, CSV export, Django Admin for question management and account provisioning.
- **Governance:** Immutable per-attempt question snapshots, secure answer-key handling in APIs, staff-only reporting, auditable events and PostgreSQL persistence.

The frontend consistently uses **DBA**, not "MSSQL"; question text may explicitly refer to SQL Server technology.

## Stack

React 19 + Vite 6 + Lucide icons (frontend); Django 5.2 + Gunicorn + WhiteNoise (API); PostgreSQL 17 (persistent source of truth); Nginx (same-origin reverse proxy); Docker Compose.

The application follows a **modular monolith** architecture for simplicity, velocity and efficiency. PostgreSQL stores users, secure sessions, questions, options, attempts, answers, results and audit history. Redis is not required in this release.

## Quick start (Ubuntu / Docker)

Prerequisites: Docker Engine and Docker Compose plugin.

```bash
git clone https://github.com/vchantha/web-quiz-dg-dba.git
cd web-quiz-dg-dba
cp .env.example .env
# Open .env and replace POSTGRES_PASSWORD and DJANGO_SECRET_KEY with real random secrets:
# python3 -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose up -d --build
docker compose ps
```

Open **http://localhost:8080** (or your server IP on port 8080).

### Create administrator and candidate users

```bash
docker compose exec backend python manage.py createsuperuser
# Then visit http://localhost:8080/admin/ and use Users > Add to create candidates.
```

Candidates should have **Active** enabled but **Staff** and **Superuser** disabled. Assessor accounts may have **Staff** enabled, and require appropriate Django admin permissions to manage records. The HR dashboard API is staff-only.

Optional local demonstration accounts are disabled by default. For local development only, set `SEED_DEMO_USERS=1` and strong `DEMO_ADMIN_PASSWORD` / `DEMO_CANDIDATE_PASSWORD` in `.env`, then restart the backend to seed **assessor** and **candidate**. **Never enable demo accounts on a public server.**

### Common operations

```bash
docker compose logs -f backend
docker compose exec backend python manage.py seed_quiz
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test
docker compose down                  # preserves the database volume
docker compose down -v               # DELETES database data: do not use in production
```

## Scoring and time enforcement

- Every question has four options, one correct choice and **4 points**.
- 25 questions × 4 points = **100 points** (13 DBA, 12 Governance).
- Default passing score: **76%** (editable from Django Admin).
- Quiz duration: **60 minutes**, enforced using the database's `expires_at` value and server time.
- Answers are committed individually to PostgreSQL using an idempotent `PUT`; candidates may resume before expiry.
- Scoring is performed transactionally and at most once. Expired attempts are scored when the backend is next contacted, including automatic submission by the UI timer.
- `QUIZ_MAX_ATTEMPTS=1` by default; change only with recruitment approval.
- Correct answers and explanations are never included in pre-submit candidate responses; post-submit review is disabled unless `QUIZ_SHOW_ANSWER_REVIEW=1`.

### API surface

| Method | Endpoint | Role |
|---|---|---|
| GET | `/api/health` | Public health check |
| GET | `/api/auth/session` | Session bootstrap + CSRF |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Authenticated |
| GET | `/api/assessments` | Authenticated |
| POST | `/api/attempts` | Candidate |
| GET | `/api/attempts/current` | Candidate |
| GET | `/api/attempts/<id>` | Owner / staff |
| PUT | `/api/attempts/<id>/answers/<question_id>` | Owner |
| POST | `/api/attempts/<id>/submit` | Owner |
| GET | `/api/results/<id>` | Owner / staff |
| GET | `/api/admin/summary` | Staff |
| GET | `/api/admin/results.csv` | Staff |
| / | `/admin/` | Django staff admin |

## Data model

- **Quiz** → published quiz definition, version, duration, pass threshold
- **Question / Option** → categorized question bank and grading criteria
- **Attempt** → user, start/deadline, immutable JSON snapshot of published questions, status and total score
- **Answer** → exactly one persisted selection per attempt/question, with change timestamp
- **AuditEvent** → login, logout, attempt start, finalization and staff export
- **Django auth + sessions** → users, password hashes, roles, CSRF/session identity

All schema changes go through Django migrations. The idempotent `seed_quiz` command loads 25 questions and does not overwrite questions already maintained by assessors. Published question changes do not alter existing attempt snapshots. For future releases, create a new quiz version rather than silently changing an in-use assessment.

## Deployment security checklist

1. Replace every secret in `.env`; never commit `.env`. Use a secret manager in production.
2. Put the app behind HTTPS (reverse proxy / ingress). Set `SESSION_COOKIE_SECURE=1`, `CSRF_COOKIE_SECURE=1`, proper `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to the final HTTPS domain.
3. Restrict administrator access; provision candidate accounts individually and enforce a recruitment data-retention policy.
4. **Important for a public repository:** this repository includes the example question bank and correct answer keys. To use it for a confidential hiring exam, make the repository private or move question-bank/answer-key provisioning into a restricted private source before inviting candidates.
5. Change or revoke demo users, use strong credentials, enforce rate limits at the reverse proxy/identity provider, configure email-based invitations/SSO when needed and monitor access.
6. Configure PostgreSQL backups, test restore operations and persist the `postgres_data` volume. Do not use `docker compose down -v` unless intentionally erasing data.
7. Use a managed database and HTTPS-enabled load balancer/ingress for real candidate traffic. This Compose deployment is a single-host starting point, not a high-availability system.

### Database backup & restore

```bash
# Backup (supply database password through your trusted environment, not command history)
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom > quiz-backup.dump
# Restore into a fresh, suitably configured target database:
cat quiz-backup.dump | docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists
```

In the commands above, `POSTGRES_USER` and `POSTGRES_DB` must be set in the shell that runs Docker Compose (or replaced with their actual configured values). Restore carefully: `--clean` removes existing objects.

## Local development

```bash
# Backend: use a running PostgreSQL and export the environment settings from .env
cd backend && pip install -r requirements.txt
python manage.py migrate && python manage.py seed_quiz
python manage.py runserver 0.0.0.0:8000
# Frontend in another terminal:
cd frontend && npm install && npm run dev
```

Vite proxies `/api` to Django for local development. Frontend build: `npm run build`. Backend integration tests: `python manage.py test`. GitHub Actions validates Django checks and migrations, integration tests, React build and Docker builds.

## Current boundaries

This release includes the five requested candidate screens and core assessor workflow. For a larger hiring program, add invitation-email delivery, per-candidate invitation expiry, password reset/SSO, proctoring policy, private exam-bank delivery, structured retention jobs, application-level throttling, and end-to-end browser tests before exposing the service to untrusted public traffic.

## Docker Desktop / Windows startup fix

If the backend logs show `exec /app/entrypoint.sh: no such file or directory` while the Dockerfile copies the file successfully, the common cause is **Windows CRLF line endings**. The Linux interpreter can interpret `#!/bin/sh\r` as a nonexistent path. This repository now enforces LF for shell scripts, normalizes `entrypoint.sh` during the Docker image build, and invokes it via `/bin/sh`. CI also builds and starts the stack with a deliberately CRLF-converted entrypoint to prevent regressions.

Update and rebuild the backend image without touching your persistent PostgreSQL volume:

```bash
git pull origin main
docker compose build --no-cache backend
docker compose up -d --force-recreate backend web
docker compose ps
docker compose logs --tail=80 backend
root / PnzU2G3u80MR
user1: B62HaI3l606O
user2: J43ZGQ1u8he9
user3: oNRcg7Q5z1pc
```

**Do not run** `docker compose down -v`: it deletes the PostgreSQL volume and candidate data.
