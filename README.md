# AfriDev Hub — Show. Solve. Prove.

AfriDev Hub is a community platform for African developers. It turns real field experience
into verifiable knowledge and auditable reputation:

1. **Show** — publish projects with their stack, country context and collaboration mode.
2. **Solve** — document the real problems developers hit (mobile money, KYC, SMS,
   connectivity) and collect concrete solutions.
3. **Prove** — accepted solutions become field reports, confirmed by developers from the
   same country, and feed an append-only reputation ledger, leaderboards and the Country Cup.

Built for CADEV2026 as a complete, runnable monorepo (frontend, API, database, Docker, CI,
demo seed and read-only MCP tools).

Highlights: three project modes (Showcase / Feedback / Open to contributors) with swipe or
button actions, an Africa activity map, contextual country and mission rooms, in-app
notifications, a low-bandwidth mode wired to the browser data-saver signal, three ownership
verification methods (GitHub owner, challenge file, domain token) and a weekly Country Cup
scored on average points per active member.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS 4, React Router, TanStack Query, Zustand, React Hook Form + Zod, i18next (FR default / EN), Lucide, Vitest + Testing Library |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, asyncpg/SQLite, WebSockets, GitHub OAuth, pytest, Ruff |
| Data | PostgreSQL 16 (production), SQLite (local/tests), 27 tables |
| Ops | Docker multi-stage images, Docker Compose, GitHub Actions CI |

## Quick start (local, no Docker)

```bash
# 1. API on http://localhost:8000
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # set DATABASE_URL=sqlite+aiosqlite:///./afridev.db for zero setup
alembic upgrade head
python scripts/seed_demo.py   # 60 demo developers, 40 projects, 25 problems, ...
uvicorn app.main:app --reload --port 8000

# 2. Web app on http://localhost:3000 (second terminal)
cd frontend
npm ci
npm run dev
```

Sign in with the demo button on `/login` (leave the username empty to create a guest
account, or use an existing demo account such as `demo-admin` with "Sign in as
administrator"). Real GitHub sign-in requires an OAuth App — see
[docs/development.md](docs/development.md).

## Quick start (Docker Compose)

```bash
export SECRET_KEY="$(openssl rand -hex 32)"
docker compose up --build
# web http://localhost:8080, API http://localhost:8000
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_demo.py
```

## Pages

Landing, Login, Dashboard, Discover, Project detail/create, Knowledge exchange with problem
detail and creation, Field reports and detail, Country hubs, Leaderboards (developers,
projects, Country Cup), Missions and detail, API directory and detail, Messages (WebSocket
realtime), Developer profile, Settings, Admin console.

French is the default interface language, mobile-first, keyboard navigable, with loading,
error and empty states on every list.

## Repository layout

```
backend/    FastAPI app (modular monolith), Alembic migrations, demo seed, pytest suite
frontend/   React SPA (feature-based), design system, i18n, Vitest tests
docs/       architecture, database, API and development guides
.github/    CI: backend lint/tests, frontend lint/typecheck/tests/build, Docker builds
```

## Documentation

- [Architecture](docs/architecture.md)
- [Database](docs/database.md)
- [API reference](docs/api.md)
- [Development guide](docs/development.md)
- [Third-party licenses](THIRD_PARTY_LICENSES.md)

## Verification status

- Backend: `ruff check app tests scripts` passes, `pytest` 15 passed, the migration applies
  on a fresh SQLite database, the demo seed runs deterministically.
- Frontend: `tsc --noEmit`, `eslint .`, `vitest run` (4 tests) and `vite build` pass.
- Not executed in this environment: `docker build` / `docker compose up` (no Docker daemon
  available) and real GitHub OAuth (no OAuth App credentials).

## Demo data

`python scripts/seed_demo.py` loads a deterministic dataset (fixed RNG seed) where every row
is flagged `is_demo` and user-facing text is prefixed `[DEMO]`. `--reset` and the admin purge
only delete demo rows: real accounts, projects and ledger entries are never touched.

## MCP tools

`backend/app/mcp` exposes read-only tools for agents: `search_field_reports`,
`search_open_projects`, `search_api_directory`.

## License

Code is provided for the CADEV2026 submission. Third-party dependencies are permissive
(MIT/ISC/BSD/Apache-2.0), with two weak-copyleft exceptions noted in
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
