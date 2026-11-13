# Development — AfriDev Hub

## Prerequisites

- Python 3.12, Node 22+ (npm 10+), and optionally Docker with Compose v2.
- No external service is required for local development: SQLite and the demo sign-in are
  enough to exercise every page.

## Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # then edit values
alembic upgrade head
python scripts/seed_demo.py     # optional demo dataset
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful commands:

```bash
ruff check app tests scripts
python -m pytest                # 15 tests
python scripts/seed_demo.py --reset   # demo rows only, never real data
```

### Environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` disables the demo sign-in |
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `DATABASE_URL` | `sqlite+aiosqlite:///./afridev.db` | Use `postgresql+asyncpg://…` for PostgreSQL |
| `SECRET_KEY` | dev value | Required in production; signs session cookies |
| `DEMO_MODE` | `true` | Enables demo data filters and the dev login |
| `FRONTEND_URL` | `http://localhost:3000` | OAuth redirect target |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | empty | Create a GitHub OAuth App to enable real sign-in |
| `GITHUB_CALLBACK_URL` | `http://localhost:8000/api/v1/auth/github/callback` | Must match the OAuth App exactly |

### Demo sign-in

`POST /api/v1/auth/dev-login` with `{"username": "amina-dev"}` creates or reuses a demo
account; `{"as_admin": true}` signs in as an administrator. The endpoint is unavailable
when `DEMO_MODE=false` or `APP_ENV=production`.

## Frontend

```bash
cd frontend
npm ci
cp .env.example .env      # VITE_API_BASE_URL=/api/v1
npm run dev               # http://localhost:3000
```

| Script | Purpose |
| --- | --- |
| `npm run dev` | Vite dev server on `0.0.0.0:3000` with `/api` and `/ws` proxied to `127.0.0.1:8000` |
| `npm run typecheck` | `tsc --noEmit` (strict) |
| `npm run lint` | ESLint (flat config, React hooks rules) |
| `npm test` | Vitest + Testing Library (jsdom) |
| `npm run build` | Typecheck then production build |

The dev server binds to `0.0.0.0`; extra preview hostnames can be allowed through
`__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS` (comma-separated) without editing tracked files.

## Docker Compose

```bash
export SECRET_KEY="change-me"
docker compose up --build
# frontend http://localhost:8080, API http://localhost:8000
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_demo.py
```

Compose runs PostgreSQL 16 with a named volume, the API as a non-root user and Nginx
serving the SPA while proxying `/api` and `/ws`. The backend image includes a health
check on `/api/v1/health`.

## Tests

- Backend: `pytest` with an isolated SQLite database per run, an autouse reference-country
  fixture and helpers for authenticated requests. Covered flows: session and CSRF,
  discovery, contribution acceptance opening a conversation, knowledge acceptance
  creating a field report and awarding points, field report confirmation rules, reputation
  caps and idempotency.
- Frontend: Vitest with Testing Library for utilities and components; provider-heavy pages
  are verified through typecheck and the production build.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `SettingsError` mentioning `cors_origins` | `CORS_ORIGINS` must be a comma-separated string, not a JSON list |
| `MissingGreenlet` on relationship access | Async ORM: refresh or query related collections explicitly instead of lazy loading |
| 403 on state-changing requests | The `X-CSRF-Token` header must echo the `afridev_csrf` cookie |
| GitHub redirect fails with `redirect_uri_mismatch` | `GITHUB_CALLBACK_URL` must exactly match the OAuth App callback |
| WebSocket closes with `4401` | The session cookie was missing or expired; sign in again |
| Demo sign-in returns 404 | `DEMO_MODE` is off or `APP_ENV=production` |

## Repository conventions

- Backend modules follow `models → schemas → service → router`; services own permissions.
- Frontend features keep pages in `src/features/<domain>` and HTTP calls in
  `src/services/api.ts`; never call `axios` from a component.
- French is the default UI language; every new string must be added to both
  `src/i18n/locales/fr.json` and `en.json`.
