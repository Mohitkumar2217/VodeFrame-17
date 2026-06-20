# Production-Oriented Project Structure

This repository now follows a clearer production-ready layout with separate frontend and backend concerns.

## Top-level

- `frontend/` - Next.js application (UI + API routes)
- `backend/` - external backend services 
- `scripts/` - utility scripts

## Backend directory

- `backend/api/` - canonical Node/Express API service
- `backend/evaluations/` - Python AI evaluation service

## Recommended run commands

From repository root:

- Web app: `npm run dev` (or `npm run dev:frontend`)
- Canonical Node API: `npm run dev:api`
- TypeScript service: `npm run dev:notify`

Python AI service:

1. `cd backend/evaluations`
2. `python -m venv .venv`
3. `.\.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. `uvicorn app:app --reload --host 127.0.0.1 --port 8000`

## Migration note

Use `frontend/` as the source of truth for web app code and `backend/api/` for Node API code.
