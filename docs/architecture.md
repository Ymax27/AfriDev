# Architecture — AfriDev Hub

AfriDev Hub is a monorepo with a single-page frontend and a modular-monolith API.

```
afridev-hub/
├── backend/            FastAPI application (Python 3.12)
│   ├── app/
│   │   ├── core/       settings, database, security, logging, rate limiting, shared schemas
│   │   ├── modules/    one package per bounded context (models, schemas, service, router)
│   │   ├── api/v1/     router aggregation and versioning
│   │   ├── mcp/        read-only MCP server exposing search tools
│   │   └── main.py     application factory, middlewares, health, WebSockets
│   ├── migrations/     Alembic environment and versions
│   ├── scripts/        deterministic demo seed
│   └── tests/          pytest suite (SQLite in-memory/temporary database)
├── frontend/           React 19 + TypeScript + Vite
│   └── src/
│       ├── app/        providers, router, query client
│       ├── components/ design system + layouts
│       ├── features/   feature-based pages (one folder per domain)
│       ├── hooks/      shared data hooks
│       ├── i18n/       i18next resources (fr default, en)
│       ├── lib/        API client, utilities
│       ├── services/   typed API surface (single place for HTTP calls)
│       ├── stores/     Zustand stores (auth, UI preferences)
│       └── types/      shared TypeScript interfaces
├── docs/               architecture, database, API and development guides
└── docker-compose.yml  PostgreSQL + API + Nginx-served frontend
```

## Frontend

- **React 19 + TypeScript strict**, built with Vite. Routes are lazy-loaded per page.
- **Feature-based structure**: a page owns its components; cross-cutting UI lives in
  `components/ui` and `components/layout`. API calls only live in `services/api.ts`.
- **Server state** is owned by TanStack Query (queries keyed by resource and filters,
  mutations invalidate the affected keys). **Client state** (session user, language,
  lightweight mode, sidebar) lives in Zustand; language and preferences are persisted
  to `localStorage`.
- **Forms** use React Hook Form with Zod schemas. **i18n** uses i18next with French as the
  default language and a complete English translation.
- **Styling** is Tailwind 4 with a design-token theme (`primary` `#123B63`, `accent`
  `#16A078`, `highlight` `#F2B544`, `surface` `#F4F7FA`). Mobile-first: the app shell is a
  sidebar on large screens and an off-canvas drawer with a sticky header on small screens.
- **Accessibility**: semantic landmarks, skip link, labelled controls, `aria-*` on tabs,
  dialogs and status messages, visible focus rings, reduced-motion support.

## Backend

- **FastAPI** with Pydantic v2 schemas and SQLAlchemy 2 async ORM (`asyncpg` in
  production, `aiosqlite` for local development and tests).
- **Modular monolith**: each package under `app/modules` exposes `models.py`, `schemas.py`,
  `service.py`, `router.py` (plus focused helpers). Routers are thin: validation, permission
  checks and orchestration live in services.
- **Cross-cutting** concerns live in `app/core`: settings, async session factory, cookie
  session signing, CSRF, rate limiting, pagination, logging, custom exceptions and
  exception handlers.
- **Authentication**: GitHub OAuth App flow with signed state + PKCE, HttpOnly session
  cookie, double-submit CSRF cookie, 30-day minimum account age check. A dev-only
  `POST /auth/dev-login` endpoint exists solely when `DEMO_MODE` is on and the environment
  is not production.
- **Realtime**: WebSocket routes for conversations, country rooms and missions with
  session cookie authentication and membership checks before joining a room.
- **MCP**: a read-only server exposing `search_field_reports`, `search_open_projects` and
  `search_api_directory` over stdio.
- **Country Cup**: country ranking uses the average points earned by active members over
  the period (weekly by default) so small countries stay competitive.
- **Project traction**: only likes from eligible accounts (7+ days old, active) are
  weighted, together with accepted contributors and useful feedback; visits and GitHub
  stars are capped.
- **Ownership verification**: three methods — GitHub repository ownership (compared with
  the linked GitHub login), a challenge file in the repository, or a token published on
  the project domain.
- **Frontend**: mobile-first with an Africa activity map generated from Natural Earth
  polygons, contextual WebSocket rooms (country and mission), in-app notifications and a
  low-bandwidth mode wired to the browser's data-saver signal.

## Request lifecycle

1. Nginx (or the Vite dev proxy) forwards `/api/*` and `/ws/*` to the API.
2. Middlewares attach a request id, log a JSON line, enforce the CSRF double-submit token
   on state-changing requests and add security headers.
3. The router validates the body with Pydantic, resolves the current user from the signed
   session cookie and delegates to a service.
4. The service enforces authorization (ownership, membership, same-country rules), writes
   through repositories/ORM and records reputation transactions through the ledger service.
5. Responses are Pydantic models; errors use a stable envelope
   `{"error": {"code", "message", "details"}}`.

## Reputation and trust

The reputation ledger is append-only. A unique constraint on
`(user_id, action_type, reference_type, reference_id)` makes each award idempotent, and
caps limit farming: 100 points/day per user, 3 verified publications, 10 points from
useful votes **per solution**, 5 rewarded confirmations per field report. Self-award is
rejected.

Additional anti-cheat rules: votes and confirmations only move the ledger for accounts
older than 7 days that are active and not frozen; repeated exchanges between the same two
accounts lose value (`points / (1 + prior reciprocal awards)`, minimum 1); an account
awarding 20 transactions within 10 minutes is treated as a burst and blocked; a reported
account has its points frozen for 3 days automatically. Balances cached on
`users.reputation_points` are derived from the ledger and can be recalculated from scratch
by an administrator.

## Deployment topology

- `docker compose up --build` starts PostgreSQL, the API (port 8000) and the frontend
  (port 8080, Nginx serving the built SPA and proxying `/api` and `/ws`).
- The API runs migrations explicitly (`alembic upgrade head`) and the demo seed is opt-in
  (`python scripts/seed_demo.py`).
- Health checks: `/health` (liveness), `/api/v1/health` and `/api/v1/health/db` (readiness).
