# ResQRoute-Backend

**SIH26002 | Ministry of Development of North Eastern Region (MDoNER)**  
*Resilient Logistics & Route Intelligence Platform*

## Overview
Django REST Framework backend providing role-based authentication (Customer, Driver, Admin), Supabase PostgreSQL database connectivity, and JWT security for the ResQRoute corridor logistics network.

## Technology Stack
- **Framework:** Python 3.13 / Django 6.1
- **API Engine:** Django REST Framework + SimpleJWT
- **Database:** Supabase PostgreSQL (via `psycopg` & `dj-database-url`) with local SQLite fallback
- **Production Server:** Gunicorn & WhiteNoise (configured for Railway)

## Quick Start (Local Development)
1. Copy `.env.example` to `.env` and set your `DATABASE_URL` (optional for local SQLite testing):
   ```bash
   cp .env.example .env
   ```
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Seed test demonstration accounts:
   ```bash
   python manage.py seed_users
   ```
4. Start development server:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

## API Endpoints
- `GET /health/`: Service and database health status
- `POST /api/auth/register/`: Customer & Driver registration with role-based profiles
- `POST /api/auth/login/`: JWT authentication
- `POST /api/auth/token/refresh/`: JWT token refresh
- `GET /api/auth/me/`: Authenticated user profile retrieval
