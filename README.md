# 🌊 SIH Flood Intelligence Platform

Satellite + terrain + weather + historical-data based flood-risk intelligence platform for India.

This project is being developed for the Smart India Hackathon (SIH).

---

# 🚀 Judge Quick Start

The repository is designed so a judge can clone it and start the complete local stack with Docker Compose.

## Prerequisites

- Git
- Docker Desktop / Docker Engine with Compose
- At least 4 GB RAM available to Docker

## 1. Clone

```bash
git clone https://github.com/SIHatmpt2/sih-floods.git
cd sih-floods
```

## 2. Create local environment

```bash
cp .env.example .env
```

The committed `.env.example` contains placeholders only. **Never commit a real API key, password, token, or secret.** The real `.env` file is intentionally ignored by Git.

For integrations that require credentials, obtain the credentials from the project team and add them locally to `.env`.

## 3. Start the complete stack

```bash
docker compose up --build
```

This starts:

- React/Vite frontend: http://localhost:5173
- Django API: http://localhost:8000
- PostgreSQL + PostGIS: localhost:5432
- Redis: localhost:6379
- MinIO API: http://localhost:9000
- MinIO console: http://localhost:9001
- Celery worker

The backend Docker image installs the geospatial system dependencies required by the Django application. fileciteturn7file0

The Compose configuration wires the frontend, backend, worker, PostGIS database, Redis, and MinIO together. fileciteturn5file0

## 4. Check the application

Open:

```text
http://localhost:5173
```

API:

```text
http://localhost:8000
```

To stop the stack:

```bash
docker compose down
```

To stop it and remove persisted Docker volumes:

```bash
docker compose down -v
```

> `docker compose down -v` deletes the local PostgreSQL and MinIO data created by the demo environment.

## Without Docker

The frontend is a Vite/React application with `dev`, `build`, and `preview` scripts. fileciteturn6file0

For the recommended judging path, use Docker Compose because the project also depends on PostgreSQL/PostGIS, Redis, MinIO, Django, and Celery. fileciteturn5file0

---

# 🔐 Environment & API Credentials

Do not put secrets in:

- `.env.example`
- `README.md`
- source files
- Docker Compose files
- screenshots
- Git history

Use:

```text
.env                # local secrets, never committed
.env.example        # safe placeholders, committed
```

The current environment template includes optional provider credentials and a `ZUPLO_CONSUMER_API_KEY` placeholder. The real Zuplo key must be supplied outside GitHub. fileciteturn0file0

If a credential has already been committed to Git history, rotate/revoke it before using the replacement credential.

---

# 🧪 Recommended Judging Checklist

1. Clone the repository.
2. Create `.env` from `.env.example`.
3. Add any credentials supplied by the team.
4. Run `docker compose up --build`.
5. Open `http://localhost:5173`.
6. Confirm the frontend can reach the Django API.
7. Exercise the flood-risk dashboard and available data/model flows.

---

# 🌍 Project Overview

The system analyzes major flood-risk drivers including glacier/snowmelt, river overflow and extreme rainfall, cyclone-related conditions, and construction/land-use change.

The platform combines geospatial data, satellite imagery, terrain, weather information, historical data, and machine-learning models to produce flood-risk maps and supporting explanations.

---

# 🧱 Core Architecture

```text
Frontend (React/Vite)
        ↓
Django REST API
        ↓
PostgreSQL + PostGIS
        ↓
Geospatial Processing
        ↓
ML Inference
        ↓
Satellite / Terrain / Weather / Historical Data
```

Supporting services:

- Redis
- Celery
- MinIO
- Docker
- PostgreSQL/PostGIS

---

# 👥 Team Responsibilities

## Frontend Developer

Responsible for:

- Dashboard
- Interactive map
- Layer controls
- Flood-risk visualization
- Time-series visualization
- Satellite image visualization
- Region selection
- Risk-score display
- Alerts
- Model-result visualization
- API integration
- Loading/error states

Recommended stack:

- React
- Vite
- TypeScript
- Tailwind CSS
- MapLibre GL JS or Leaflet
- Recharts / ECharts

Frontend should NOT implement ML logic. The frontend consumes Django REST APIs.

Example endpoints:

```text
GET /api/v1/regions/
GET /api/v1/risk/
GET /api/v1/flood-events/
GET /api/v1/satellite/
GET /api/v1/forecast/
```

## Backend / API Developer

Responsible for:

- Django configuration
- Django REST Framework
- Authentication
- API endpoints
- Database integration
- Celery tasks
- ML inference endpoints
- Data ingestion endpoints
- File/object storage integration
- API validation
- API documentation

## Database Developer

Use PostgreSQL + PostGIS. Do not store large satellite rasters directly in PostgreSQL; store large raster/object data in MinIO or external object storage and keep metadata/references in PostgreSQL.

## AI / ML Developer

Responsible for:

- Dataset preparation
- Satellite preprocessing
- Feature engineering
- Model training
- Model evaluation
- Model serialization
- Inference pipeline
- Model versioning

The ML pipeline should initially prioritize a working demo over maximum scientific complexity.

---

# 🤖 ML Architecture

The intended design uses specialized models/pipelines rather than one monolithic model.

## Flood Segmentation

Purpose: detect flooded regions from satellite imagery.

Potential inputs include Sentinel-1 SAR and Sentinel-2 optical imagery where cloud-free data are available.

## Flood Risk Model

Purpose: estimate flood risk using rainfall, accumulated rainfall, rainfall anomaly, elevation, slope, distance to river, river water level, land cover, historical flood frequency, soil/terrain features, built-up percentage, cyclone indicators, and glacier/snow indicators.

Output:

```text
risk_score ∈ [0, 1]

LOW
MODERATE
HIGH
SEVERE
```

XGBoost is preferred for the initial tabular risk model because it is fast to train and explain.

## Construction Change Detection

Use satellite change detection to identify new or expanded built-up areas. A feature-based approach is acceptable for the initial demo.

## Glacier Change

Use satellite segmentation and temporal analysis to estimate glacier/snow/ice area change. Present this as a contributing risk factor rather than claiming deterministic flood prediction.

## Cyclone Risk

Use cyclone/weather data and engineered features such as position, distance to coast, wind speed, pressure, rainfall, direction, and landfall proximity.

---

# 🛰️ Open Satellite Datasets

## Sentinel-1

Primary flood-detection satellite using Synthetic Aperture Radar (SAR).

Source: https://dataspace.copernicus.eu/

## Sentinel-2

Primary optical satellite for RGB, NIR, SWIR, NDVI, NDWI, NDBI, land-cover, and change analysis.

Source: https://dataspace.copernicus.eu/

## Landsat Collection 2

Useful for historical analysis, long-term land-use change, glacier/snow analysis, and construction change.

Source: https://www.usgs.gov/landsat-missions/landsat-data-access

---

# ⛰️ Terrain / Elevation Datasets

## Copernicus DEM GLO-30

Primary DEM for elevation, slope, aspect, drainage, watershed analysis, and terrain risk.

Source: https://dataspace.copernicus.eu/

## SRTM

Alternative/supplementary elevation dataset for elevation, slope, and terrain analysis.

Source: NASA / USGS

---

# 🌧️ Rainfall / Weather Data

## NASA GPM IMERG

Useful for precipitation, accumulated rainfall, extreme rainfall, and rainfall anomalies.

Source: https://gpm.nasa.gov/data

## ERA5

Useful for temperature, wind, pressure, humidity, and atmospheric variables.

Source: https://cds.climate.copernicus.eu/

---

# 🗺️ OpenStreetMap

Use OpenStreetMap for roads, buildings, waterways, bridges, settlements, and infrastructure context.

Source: https://www.openstreetmap.org/

Do not scrape public OSM servers aggressively. For larger datasets, use appropriate regional extracts or providers.

---

# 📚 Historical Flood Datasets

Historical flood information should be used for model labels, validation, historical frequency, and risk scoring.

Potential sources include:

- NASA flood products
- Copernicus Emergency Management Service
- Sentinel-derived flood maps
- publicly available flood-event datasets
- government datasets where licensing permits
- research datasets such as Sen1Floods11

Every dataset used for training should record its source, license, acquisition date, and preprocessing steps.

---

# ⚠️ Important Security Note

GitHub Push Protection is enabled for this repository's detected secret pattern. **Do not bypass push protection by publishing an active API credential.** Remove secrets from Git history and rotate credentials that were exposed.

For judging, provide live credentials separately to authorized judges only, or use a demo/offline mode that does not require private credentials.
