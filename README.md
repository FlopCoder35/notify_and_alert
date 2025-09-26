Alerting & Notification Platform (Django + DRF)

Quickstart
- Create venv and install deps (Windows PowerShell):
  - python -m venv .venv
  - .\.venv\Scripts\python -m pip install -r requirements.txt
- Run initial setup:
  - .\.venv\Scripts\python manage.py migrate
  - .\.venv\Scripts\python manage.py seed_data
  - .\.venv\Scripts\python manage.py runserver

Credentials
- Admin: username: admin, password: password

API Endpoints (MVP)
- Admin
  - POST /api/alerts/
  - PATCH /api/alerts/{id}/
  - GET /api/alerts/?severity=&archived=&reminders_enabled=&visibility=
  - POST /api/alerts/{id}/deliver_now/
- User
  - GET /api/my-alerts/
  - POST /api/my-alerts/{pref_id}/read/ {"is_read": true|false}
  - POST /api/my-alerts/{pref_id}/snooze/ {"snooze_for_today": true}
- Analytics
  - GET /api/analytics/

Reminder Logic
- Management command: .\.venv\Scripts\python manage.py trigger_reminders
- Send reminders every 2 hours by default, skipping if read or snoozed today.
- Snooze resets the next day.

Extensibility
- Strategy pattern for channels in `notifications/services.py` (add Email/SMS easily).
- Visibility handled in `Alert` with org/team/user targeting.


