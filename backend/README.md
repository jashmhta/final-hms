HMS Backend (Django + DRF)

Features

- Multi-tenant: per-hospital data isolation with central admin oversight
- Modules: Patients, Appointments (slots), EHR (notes, attachments), Users/Roles, HR (roster/leaves), Facilities (wards/beds), Pharmacy (inventory/prescriptions/dispense), Lab (tests/orders/results), Billing (bills/items/payments/services), Analytics, Feedback, Audit Logs
- Auth: JWT with role-based access
- API Docs: Swagger at /api/docs/ (Bearer auth)
- Security: HTTPS-ready settings, throttling, audit logging
- DevOps: Docker, docker-compose, health check at /health/

Local dev

- python3 -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt
- cp .env.example .env
- python manage.py migrate
- python manage.py seed_initial
- python manage.py runserver 0.0.0.0:8000

Docker compose

- docker compose up -d --build
- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs at /api/docs/)

Env vars

- DJANGO_SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS
- DB: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
- JWT_ACCESS_MIN, JWT_REFRESH_DAYS, JWT_SIGNING_KEY
- SECURITY: SECURE_HSTS_SECONDS, DEFAULT_FROM_EMAIL, ADMIN_EMAIL

Testing

- pytest

Notes

- For production, configure HTTPS termination at the ingress/load balancer and set secure cookies (default enabled when DEBUG=false).
- Use object storage (S3) for media/attachments in production via django-storages.
