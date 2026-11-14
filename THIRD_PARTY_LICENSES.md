# Third-party license audit

Audit date: 2026-11-13. Method: `pip-licenses` for the backend virtualenv and a scan of every
`node_modules/*/package.json` license field for the frontend (direct and transitive
dependencies, including dev/build tooling).

## Backend (Python, 50 packages)

| License | Packages |
| --- | --- |
| MIT | 22 |
| BSD-3-Clause | 12 |
| MIT License (declared variant) | 7 |
| Apache-2.0 | 4 |
| BSD License (2/3 clause variants) | 2 |
| Apache-2.0 OR BSD-2-Clause / OR BSD-3-Clause | 2 |
| PSF-2.0, MIT AND PSF-2.0, MIT-0 | 3 |
| MPL-2.0 | 1 (`certifi`) |

Runtime libraries: FastAPI (MIT), Starlette (BSD-3-Clause), Pydantic (MIT), SQLAlchemy (MIT),
asyncpg (Apache-2.0), aiosqlite (MIT), Alembic (MIT), httpx (BSD-3-Clause), itsdangerous
(BSD-3-Clause), MCP SDK (MIT), uvicorn (BSD-3-Clause), pytest (MIT), Ruff (MIT).

## Frontend (Node, 186 packages in `node_modules`)

| License | Packages |
| --- | --- |
| MIT | 151 |
| ISC | 11 |
| BSD-2-Clause | 8 |
| Apache-2.0 | 7 |
| BSD-3-Clause | 3 |
| MPL-2.0 | 2 (`lightningcss`, `lightningcss-linux-x64-gnu`) |
| BlueOak-1.0.0 | 2 (`graceful-fs`, `minimatch`) |
| 0BSD | 1 |
| CC-BY-4.0 | 1 (`caniuse-lite`) |

Map geometry: `frontend/src/features/countries/africa-map-data.ts` is generated from the
Natural Earth 1:110m country polygons, released in the **public domain** by Natural Earth
(no attribution required; credited in the UI and in this file).

Runtime libraries: React and React DOM (MIT), React Router (MIT), TanStack Query (MIT),
Zustand (MIT), Axios (MIT), React Hook Form (MIT), Zod (MIT), i18next / react-i18next (MIT),
Lucide (ISC), Tailwind CSS (MIT).

## Findings

- No GPL, AGPL or SSPL dependency is present, in either the runtime or the build toolchain.
- **MPL-2.0** (`certifi`, `lightningcss`): weak, file-level copyleft. Used unmodified as a
  dependency (CA bundle; Tailwind/Vite CSS transform), which is compatible with distributing
  this project under its own terms. No obligation to publish our source.
- **CC-BY-4.0** (`caniuse-lite`): build-time browser data only, never shipped to users.
  Attribution is preserved by keeping the package and its notice in `node_modules` /
  `package-lock.json`.
- **BlueOak-1.0.0** (`graceful-fs`, `minimatch`): permissive, no attribution requirement.
- No dependency is paid, license-gated or requires a commercial agreement.

## Reproduce

```bash
cd backend && . .venv/bin/activate && pip-licenses --summary
cd frontend && node -e "for (const p of require('fs').readdirSync('node_modules')) { \
  try { const j = require('./node_modules/' + p + '/package.json'); \
  console.log(p, j.license || 'UNKNOWN'); } catch {} }" | sort -k2
```
