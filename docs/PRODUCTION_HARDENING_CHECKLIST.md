# Production hardening checklist

- Keep provider/API secrets in environment configuration only.
- Run `python manage.py check` in the deployed environment.
- Run `python manage.py makemigrations --check` before release.
- Apply migrations before serving traffic.
- Run the backend test suite with PostGIS and Redis available.
- Run Celery worker and beat against the same Redis broker configuration.
- Keep model training out of HTTP request handling.
- Validate model artifacts before loading them for inference.
- Monitor Weather freshness and Risk data quality fields.
- Do not commit large raw datasets or generated model binaries unless explicitly required.
