---
tags: [readme, overview, 概览]
aliases: [项目概览, Overview]
---

# Integrated Education Platform

An all-in-one classroom-friendly Python learning platform for LAN classrooms, school labs, and small teaching groups.

It combines a student-facing game-like learning flow with a teacher-facing admin console, local-first deployment, real-time PvP battles, and persistent learning records.

[简体中文](README.zh-CN.md)

---

## Overview

This project is designed for offline or intranet teaching scenarios where a teacher needs to:

- run a local classroom server
- manage students and question banks
- guide students through structured learning paths
- review records, mistakes, and rankings
- host real-time PvP quiz battles

It is not a generic LMS, a cloud SaaS product, or a code execution sandbox.

---

## Core Features

### Student App

- Login and registration
- Home navigation page
- Adventure mode with units and levels
- Random practice mode
- Extreme challenge mode
- Leaderboards
- Achievement wall
- Learning records and wrong-question review
- PvP lobby, room, battle, and result flow
- Account center

### Teacher Admin

- Admin login
- Dashboard and classroom KPIs
- Student management
- Question, unit, and level management
- Teaching analytics
- Wrong-question statistics
- PvP room management
- Import center

### Platform Layer

- FastAPI backend
- Vue 3 + TypeScript frontend
- SQLite persistence
- WebSocket-based online status and PvP sync
- Windows-first local startup
- PyInstaller packaging support

---

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | Vue 3, TypeScript, Vite, Pinia, Vue Router |
| Backend | FastAPI, SQLAlchemy |
| Database | SQLite |
| Realtime | WebSocket |
| Testing | Pytest, Vitest, Playwright |
| Packaging | PyInstaller |

---

## Repository Structure

```text
backend/
  app/
    main.py            FastAPI entrypoint
    __main__.py        CLI entrypoint
    cli.py             migration commands
    database.py        engine / session / Base
    deps.py            auth dependencies
    models/            ORM models
    schemas/           Pydantic schemas
    routers/           HTTP routers
    services/          business logic
    ws/                WebSocket logic
  alembic/             migrations
  tests/               backend tests

frontend/
  src/
    main.ts            Vue entrypoint
    router/            route config
    stores/            Pinia stores
    api/               HTTP client layer
    views/             page views
    components/        shared UI components

docs/
  PRD.md
  ARCHITECTURE.md
  API.md
  DATABASE.md
  UI_SPEC.md
  AGENTS.md
```

---

## Quick Start

### Requirements

- Windows is the primary maintenance environment
- Python `>= 3.12`
- Node.js and npm
- `uv` recommended for Python dependency management

### Backend

```powershell
uv sync --directory backend
cd backend
uv run python -m app
```

### Frontend Development

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

### One-Click Local Startup

```powershell
start.bat
```

Default URLs:

- Student app: `http://localhost/app/`
- Teacher admin: `http://localhost/app/admin`

Default admin account:

- Username: `admin`
- Password: `admin123`

The admin account is auto-seeded on first run and should change the password immediately after first login.

---

## Common Commands

```powershell
# Frontend build
npm --prefix frontend run build

# Frontend unit tests
npm --prefix frontend run test

# Frontend E2E tests
npm --prefix frontend run test:e2e

# Backend tests
cd backend
uv run pytest tests/ -v

# Migration status
cd backend
uv run python -m app migrate --status

# Apply migrations
cd backend
uv run python -m app migrate --upgrade
```

---

## Runtime Facts

- The frontend is served under `/app/`
- The backend exposes both `/api/v1/*` and `/api/*`
- The online WebSocket endpoint is `/ws/online`
- `/` redirects to `/app/`
- `/admin` redirects to `/app/admin`
- The teacher admin currently lives inside a single Vue page with internal tabs

---

## Documentation Map

Use these documents as the source of truth:

1. [docs/PRD.md](docs/PRD.md)
   Product goals, roles, feature scope, business rules
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
   Code structure, runtime entrypoints, routing, system boundaries
3. [docs/API.md](docs/API.md)
   HTTP APIs, WebSocket messages, auth and error conventions
4. [docs/DATABASE.md](docs/DATABASE.md)
   Tables, relationships, migration constraints
5. [docs/UI_SPEC.md](docs/UI_SPEC.md)
   Student/admin UI rules, layout, visual system, responsive limits
6. [docs/AGENTS.md](docs/AGENTS.md)
   Public collaboration notes for future maintainers or AI agents

For public contributors, use [docs/AGENTS.md](docs/AGENTS.md) as the collaboration entrypoint.

---

## Development Notes

- Student-visible business truth must come from the server
- PvP and answer validation are server-authoritative
- Frontend changes should at least pass a build
- Backend changes should at least pass the closest relevant validation
- Public-facing docs should only link to public documents under `docs/` or the README files themselves

---

## Public Repository Notes

Usually kept in the public repository:

- source code
- public documentation
- public changelog

Usually kept local-only:

- internal changelog
- agent memory and local AI collaboration notes
- review notes and temporary drafts
- database files
- build outputs

---

## License

See [LICENSE](LICENSE).

---

> 📍 [[docs/HOME|文档地图]] · [[README.zh-CN|中文说明]]
