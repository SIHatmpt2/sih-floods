# SIH Flood Intelligence Platform

Django-based flood intelligence platform with a server-rendered HTML/CSS/JavaScript frontend.

## Project layout

- `backend/` — Django project, REST APIs, risk/weather apps, Celery tasks, and ML integrations.
- `backend/templates/` — Django HTML templates.
- `backend/static/` — frontend CSS, JavaScript, and images.
- `data/` — project datasets and processing assets.
- `docker/` — Django/container build definitions.

The React/Vite frontend has been removed from the runtime architecture. Django serves the public web UI from `/` while existing APIs remain under `/api/`.

## Run locally

From `backend/`:

```powershell
python manage.py check
python manage.py migrate
python manage.py runserver 8000
```

Open `http://127.0.0.1:8000/`.

## API and health endpoints

- `/api/core/`
- `/api/risk/`
- `/api/weather/`
- `/api/schema/`
- `/api/docs/`
- `/health/`
- `/health/ready/`
- `/health/live/`

## Docker

The Compose stack keeps Django, Celery, PostGIS, Redis, and MinIO. There is no separate Node/Vite frontend service; Django serves the frontend directly.

```powershell
docker compose up --build
```

The web application is available at `http://localhost:8000/`.
