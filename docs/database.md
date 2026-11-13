# Database — AfriDev Hub

PostgreSQL 16 is the production target; SQLite (`aiosqlite`) is supported for local
development, tests and the demo seed. The ORM uses portable types (`Uuid`, `JSON`,
`DateTime(timezone=True)`) so the same models run on both engines.

Schema is versioned with Alembic. The initial migration
(`migrations/versions/6d05700d8643_initial_schema.py`) creates **26 tables**, including
`alembic_version`.

## Tables

| Table | Purpose |
| --- | --- |
| `users` | Developer accounts, GitHub identity, country, reputation cache, admin/demo flags |
| `user_roles` | Declared roles (`developer`, `maintainer`, `mentor`, `student`, `sponsor`) |
| `user_skills` | Skills with level and years of experience |
| `countries` | Reference countries with ISO code, French/English names, flag and region |
| `projects` | Showcased projects, stack, collaboration mode, ownership status, counters |
| `project_likes` / `project_passes` | Discovery interactions, unique per user and project |
| `contribution_requests` | Requests to contribute with a domain and status workflow |
| `project_feedback` | Structured feedback (concept / improvement / feature) with usefulness flag |
| `ownership_verifications` | Repository-file challenge tokens and verification status |
| `knowledge_problems` | Field problems with category, technology, API link and country |
| `solutions` | Proposed solutions with code, steps, references and acceptance flag |
| `field_reports` | Validated knowledge artefacts derived from accepted solutions |
| `field_report_confirmations` | Same-country confirmations with comments |
| `api_providers` / `api_entries` | API directory entries, coverage, status, integration notes |
| `missions` / `mission_submissions` | Sponsored missions and developer submissions with review |
| `reputation_transactions` | Append-only reputation ledger |
| `conversations` / `conversation_members` / `messages` | Private messaging |
| `notifications` | In-app notifications |
| `content_reports` | Moderation reports (resolved / dismissed) |
| `user_blocks` | Blocked users |
| `alembic_version` | Migration bookkeeping |

## Key relationships

```
countries 1─* users 1─* projects 1─* project_likes / project_passes
                         projects 1─* contribution_requests *─1 users
                         projects 1─* project_feedback *─1 users
                         projects 1─* ownership_verifications
knowledge_problems 1─* solutions 1─0..1 field_reports
field_reports 1─* field_report_confirmations *─1 users
api_entries *─1 api_providers ; api_entries 1─* knowledge_problems
missions 1─* mission_submissions *─1 users
users 1─* reputation_transactions
conversations *─* users (conversation_members) ; conversations 1─* messages
```

Foreign keys use `ON DELETE CASCADE` where the child cannot exist without the parent
(solutions, members, likes) and `SET NULL` for optional references (e.g. a field report
kept after its problem is removed).

## Constraints and indexes

- Unique: `users.username`, `users.github_id`, `countries.code`, `projects.slug`,
  `(project_likes.user_id, project_likes.project_id)`,
  `(project_passes.user_id, project_passes.project_id)`,
  `(conversation_members.conversation_id, conversation_members.user_id)`.
- Check: reputation points bounds, non-negative counters, valid enum values (stored as
  strings for portability).
- Indexes on foreign keys and on frequently filtered columns: `projects.collaboration_mode`,
  `projects.created_at`, `knowledge_problems.category`, `field_reports.status`,
  `reputation_transactions.user_id`.
- `reputation_transactions` has a unique constraint on
  `(user_id, action_type, reference_type, reference_id)`: the same fact can never be
  awarded twice.

## Reputation ledger

`reputation_transactions` is append-only: rows are inserted, never updated to change
points. `users.reputation_points` is a cache refreshed by the ledger service after each
award and can be rebuilt from transactions:

```
python -c "import asyncio; from app.core.database import SessionLocal; \
from app.modules.reputation.service import recalculate_all; \
asyncio.run(recalculate_all(SessionLocal))"
```

Caps enforced by the service:

| Rule | Limit |
| --- | --- |
| Total points per user per day | 100 |
| Verified publications per day | 3 |
| Points from useful votes per day | 10 |
| Rewarded confirmations per field report | 5 |
| Self-awarded points | rejected |

## Field report lifecycle

`published` → `confirmed` once the confirmation threshold is reached. A report whose
`last_validated_at` is older than 90 days is flagged `needs_revalidation` (a scheduler or
cron job can update this; nothing is deleted). Archived reports remain readable.

## Demo data

Every seeded row carries an `is_demo` flag and `[DEMO]` prefixes in user-facing text.
`scripts/seed_demo.py --reset` only deletes demo rows and their dependent demo children;
real accounts, projects and ledger entries are never removed. The admin "purge demo data"
action follows the same rule.

## Migrations

```bash
cd backend
alembic upgrade head          # apply
alembic revision --autogenerate -m "change"   # create
alembic downgrade -1          # roll back one step
```
