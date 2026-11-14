# API — AfriDev Hub

Base URL: `/api/v1`. Interactive documentation is served by FastAPI at `/docs` and the
OpenAPI document at `/openapi.json`.

## Conventions

- JSON in, JSON out. Timestamps are ISO-8601 UTC. Identifiers are UUID strings.
- Lists return `{"items": [...], "total": n, "page": p, "page_size": s}` and accept
  `page`, `page_size` (max 100), `q`, `country`, `category`, `technology`, `mode`,
  `status`, `sort` depending on the resource.
- Errors use `{"error": {"code": "not_found", "message": "...", "details": {...}}}` with
  appropriate HTTP status codes (`400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`).
- Authentication is the `afridev_session` HttpOnly cookie. State-changing requests must
  echo the `afridev_csrf` cookie in the `X-CSRF-Token` header (double-submit).

## Authentication

| Method | Path | Description |
| --- | --- | --- |
| GET | `/auth/status` | Whether a session exists, whether GitHub OAuth is configured, demo mode |
| GET | `/auth/github` | Returns the GitHub authorization URL (signed state + PKCE) |
| GET | `/auth/github/callback` | Exchanges the code, enforces account age, sets the session |
| POST | `/auth/dev-login` | Demo-only sign-in (`{"username": "...", "as_admin": false}`) |
| GET | `/auth/me` | Current user or 401 |
| GET | `/auth/me/optional` | Current user or `null` |
| POST | `/auth/logout` | Clears the session cookie |

`/auth/dev-login` returns 404 unless `DEMO_MODE=true` and the environment is not
production.

## Users and reputation

| Method | Path | Description |
| --- | --- | --- |
| GET | `/users` | Search developers |
| GET | `/users/me` | Full profile with counters |
| PATCH | `/users/me` | Update profile, country, skills, roles |
| GET | `/users/{username}` | Public profile |
| GET | `/reputation/me` | Points, level, next level and recent ledger entries |
| GET | `/reputation/transactions` | Own ledger entries (paginated) |
| GET | `/reputation/transactions/{user_id}` | Public ledger entries for a user |

## Countries

| Method | Path | Description |
| --- | --- | --- |
| GET | `/countries` | Reference list with codes, names and flags |
| GET | `/countries/{code}` | Hub: stats, top developers, recent projects/reports, open missions |

## Projects and discovery

| Method | Path | Description |
| --- | --- | --- |
| GET | `/projects` | Filter by `q`, `country`, `category`, `technology`, `mode`, `creator` (username), `sort` |
| GET | `/projects/discover` | Feed excluding projects the user liked or passed |
| POST | `/projects` | Create a project (authenticated) |
| GET | `/projects/{id}` | Project detail (increments the view counter) |
| PATCH | `/projects/{id}` | Owner-only update |
| DELETE | `/projects/{id}` | Owner-only delete |
| POST | `/projects/{id}/like` | Idempotent like |
| POST | `/projects/{id}/pass` | Idempotent pass |
| GET | `/projects/{id}/feedback` | Structured feedback |
| POST | `/projects/{id}/feedback` | Submit feedback (feedback mode) |
| POST | `/projects/{id}/feedback/{feedback_id}/useful` | Mark a feedback as useful (awards points) |
| POST | `/projects/{id}/ownership-verification` | Start a repository-file challenge |
| POST | `/projects/{id}/ownership-verification/{verification_id}/confirm` | Confirm ownership |

## Contributions

| Method | Path | Description |
| --- | --- | --- |
| POST | `/projects/{id}/contributions` | Request to contribute (`domain`, `message` ≥ 20 chars) |
| GET | `/contributions/me` | Own requests |
| GET | `/projects/{id}/contributions` | Requests for a project (owner or accepted members) |
| POST | `/contributions/{id}/accept` | Owner accepts, opens a conversation, awards points |
| POST | `/contributions/{id}/reject` | Owner rejects |
| POST | `/contributions/{id}/merged` | Owner marks the contribution merged |

## Knowledge exchange

| Method | Path | Description |
| --- | --- | --- |
| GET | `/knowledge` | Problems with `q`, `country`, `category`, `technology` |
| POST | `/knowledge` | Publish a problem |
| GET | `/knowledge/{id}` | Problem with its solutions |
| POST | `/knowledge/{id}/solutions` | Propose a solution |
| POST | `/knowledge/{id}/solutions/{solution_id}/accept` | Author accepts: creates a field report, awards 20 points |

## Field reports

| Method | Path | Description |
| --- | --- | --- |
| GET | `/field-reports` | Filter by `q`, `country`, `status` |
| GET | `/field-reports/{id}` | Report detail |
| PATCH | `/field-reports/{id}` | Author update |
| GET | `/field-reports/{id}/confirmations` | Confirmations list |
| POST | `/field-reports/{id}/confirm` | Same-country confirmation (idempotent, capped rewards) |

## Knowledge votes

| Method | Path | Description |
| --- | --- | --- |
| POST | `/knowledge/solutions/{id}/vote` | Mark a solution useful: +2 to its author, capped at +10 per solution. Only accounts older than 7 days move the ledger. |

## Missions

| Method | Path | Description |
| --- | --- | --- |
| GET | `/missions` | Open missions |
| POST | `/missions` | Publish a mission (API provider, company or admin only) |
| GET | `/missions/{id}` | Mission detail |
| POST | `/missions/{id}/submissions` | Submit a solution |
| GET | `/missions/{id}/submissions` | Sponsor review list |
| POST | `/missions/submissions/{id}/review` | Approve or reject (`{"approve": true, "review_note": "..."}`) |

## API directory

| Method | Path | Description |
| --- | --- | --- |
| GET | `/apis` | Search entries (`q`, `category`, `country`) |
| GET | `/apis/categories` | Categories with counts |
| PATCH | `/apis/{id}` | Edit a sheet (its provider owner or an admin) — the directory is curated, no public creation |
| GET | `/apis/{id}` | Entry detail with related field reports count |

## Leaderboards

| Method | Path | Description |
| --- | --- | --- |
| GET | `/leaderboard/developers?period=all\|month\|week&country=SN` | Ranked developers |
| GET | `/leaderboard/projects` | Weighted project score |
| GET | `/leaderboard/countries?period=week\|month` | Country Cup: average points per active member over the period (weekly by default) |

Demo accounts are included when `DEMO_MODE` is on; pass `include_demo=false` where
supported to exclude them.

## Messaging and notifications

| Method | Path | Description |
| --- | --- | --- |
| GET | `/conversations` | Own conversations |
| GET | `/conversations/{id}/messages` | Messages (members only) |
| POST | `/conversations/{id}/messages` | Send a message |
| GET | `/notifications` | Notifications and unread count |
| POST | `/notifications/{id}/read` | Mark as read |
| POST | `/notifications/read-all` | Mark every notification as read |

## Moderation and admin

| Method | Path | Description |
| --- | --- | --- |
| POST | `/reports` | Report content |
| GET | `/blocks` | Blocked users |
| POST | `/blocks` | Block a user |
| DELETE | `/blocks/{id}` | Unblock |
| GET | `/admin/overview` | Platform counters |
| GET | `/admin/users` | Search users |
| POST | `/admin/users/{id}/suspend` / `reactivate` | Account status |
| POST | `/admin/users/{id}/freeze-reputation` / `unfreeze-reputation` | Ledger freeze |
| GET | `/admin/reports` | Moderation queue |
| POST | `/admin/reports/{id}/resolve` | Resolve or dismiss |
| POST | `/admin/reputation/recalculate` | Rebuild cached balances from the ledger |
| POST | `/admin/field-reports/revalidate` | Flag field reports untouched for 90 days (also runs at startup) |
| POST | `/admin/demo/purge` | Delete demo rows only |

## Health

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness (outside the versioned prefix) |
| GET | `/api/v1/health` | Versioned liveness |
| GET | `/api/v1/health/db` | Database readiness |

## WebSockets

Authenticated with the session cookie; unauthorized sockets close with `4401`.

| Path | Description |
| --- | --- |
| `/ws/conversations/{conversation_id}` | Members only. Client sends `{"type": "message.send", "body": "..."}`; server broadcasts `{"type": "message.created", "message": {...}}` |
| `/ws/countries/{code}` | Country room with presence; `{"type": "ping"}` gets `pong` |
| `/ws/missions/{mission_id}` | Mission room for sponsors and participants |

## MCP tools

The `app.mcp.server` module exposes three read-only tools over stdio:
`search_field_reports`, `search_open_projects` and `search_api_directory`. They reuse the
same query services as the REST API and never write.
