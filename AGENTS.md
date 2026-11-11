# Agent constraints for astroimage

This repository is opinionated. Do not introduce libraries, layers, or patterns that this file and the skills it names do not allow. CI, linters, architecture tests, and pre-commit hooks must stay green.

## Report unsolicited decisions

The user will not specify every UI, API, or implementation choice. When something is underspecified and you must pick a path to keep moving, **do not stop to ask** unless the choice would violate this file, a skill, or the stated goal.

Keep going, then **notify the user in the same turn's summary** under a heading `Decisiones no pedidas` (or `Unsolicited decisions` if the conversation is in English). For each item, state:

1. What was not specified
2. What you chose
3. Why (one line, tied to existing constraints)
4. How to change it if they disagree

Do not hide these choices in source comments. Do not skip the report because the choice felt "obvious". If there were none, omit the heading.

## Declarative Programming Guidelines

Prefer declarative expressions that describe the intended transformation or result rather than every execution step. Use `map`, `filter`, `reduce`, comprehensions, `any`, `all`, `sum`, and `next` when they are easier to read. Prefer immutable data, pure functions, values derived from existing state, small composable functions with one responsibility, and expressions that communicate intent directly.

In React, prefer composition, declarative rendering, and functional state updates. `useEffect` only synchronizes with an external system, not ordinary data derivation (effect skill below). Do not mutate React state or objects used as state. Do not keep state or effects whose only job is to mirror derived values. Do not use deeply nested conditionals or procedural rendering logic.

Do not reimplement a standard-library transformation. Avoid unnecessary imperative loops, manual accumulators, and mutable intermediate collections. Avoid monolithic functions that mix retrieval, transformation, business logic, and presentation. Avoid abstractions that obscure intent or introduce unnecessary complexity.

Do not force declarative constructs when imperative code is more readable. Do not replace a simple loop with a chain of functional operations that is harder to follow. Do not add an abstraction only to eliminate imperative syntax. Readability, maintainability, correctness, and explicit intent come before paradigm purity. Keep imperative code for I/O, resource management, and interactions with external systems.

## Documented contracts first

Prefer the documented contract of the library that owns the responsibility (public API, files it says belong in the repo, documented configuration). A style recommendation weighs less than a contract. A written decision in this file wins over a generic tutorial. Deviating needs a concrete reason: a reproduced bug, a security advisory, a platform limit, or a decision already written here.

Do not declare a conflict until both sides are quoted and they govern the same responsibility in the same situation. A default, an example, and a constraint from another layer are not a conflict. If the quotes are missing or the mechanism is still unclear, keep reading. Do not redesign and do not blame the libraries.

- Two library contracts. Different layers can both hold. The same responsibility cannot have two owners. Overlapping opinions are resolved by assigning the job to one side.
- This project against a rule it decided to follow. Ask whether that rule still makes sense here: what breaks if it is dropped, and what it costs the project if it is kept. Do not treat the mismatch as proof that the library or the project is wrong.

## Layout

- `backend/` — FastAPI API (`src/` layout, package `astroimage`)
- `frontend/` — Vite + React SPA
- `monitoring/` — external observability compose (not part of the app image)
- `sonar/` — external SonarQube compose (code quality; not part of the app image)
- Root `docker-compose.yml` — API + frontend + PostgreSQL + MinIO
- Root `sonar-project.properties` — SonarQube/SonarCloud monorepo analysis config

## Skills

Load the matching skill before that work. Do not copy its rules back into this file.

- Backend features, modules, tests, imports, architecture, session, errors, allowed stack: `.agents/skills/backend-architecture/SKILL.md`. Typing, async, logging, uv: `.agents/skills/python/SKILL.md`. Service shape stays in the backend skill.
- Components, queries, routes, client state, allowed stack, theming, exclusive choices: `.agents/skills/react-spa/SKILL.md`. Types and `tsconfig`: `.agents/skills/typescript/SKILL.md`. Effects: `.agents/skills/you-might-not-need-an-effect/SKILL.md`. Compound components and boolean props: `.agents/skills/vercel-composition-patterns/SKILL.md`.
- Image page, inspector, forms, metadata, markers, glossary: `.agents/skills/frontend-image-workspace/SKILL.md`.
- Placeholders, labels, HelpHint, toasts, empty states, errors, glossary prose, README, and delivery docs: `.agents/skills/copy/SKILL.md` before writing or reviewing that prose. The skill holds the tell list. Do not keep a second copy of it here.

## Out of current scope

- Authentication
- Rate limiting
- ARQ/Redis/Celery (defer until processing volume requires it)
- In-memory cache libraries beyond what Python already provides
- Extra compose app services beyond the root stack (API, frontend, PostgreSQL, MinIO)
- Storybook
- Kibana / Elasticsearch
- New UI kits, HTTP clients (axios, ky), or routers

## Contracts

- OpenAPI is the only API contract between backend and frontend
- After backend endpoint changes: export `backend/openapi.json` and run `pnpm generate:api` in frontend
- CORS is configured for the local Vite origin
- The API emits JSON logs and exposes `/metrics`; it does not ship Grafana/Prometheus/Loki/Tempo

## Quality gates

Every change must pass:

1. Backend: `ruff format`, `ruff check`, `mypy`, `lint-imports`, `pytest` (unit + integration + architecture; writes `coverage.xml`)
2. Frontend: `biome check`, `tsc`, `vitest` / `pnpm test:coverage`, Playwright for critical flows
3. SonarQube: CI starts an ephemeral Community server (no SonarCloud, no external token), scans with `sonar-project.properties`, and uploads `issues.json` and `issues.md`. It does not fail the build on the quality gate (no baseline). Local analysis still waits for the gate (`sonar.qualitygate.wait`).
4. Mutation testing (local completion gate, not CI yet): before marking branch work as done, run the mutation suite for the affected stack.
   - Backend: `wsl.exe -d Ubuntu -- bash -lc "cd /mnt/d/repos/tip/Astroimage/backend && UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut run --max-children 2"`.
   - Frontend: `pnpm test:mutation:lib` for `src/lib`; the matching `test:mutation:catalogs` / `test:mutation:images` script for feature changes.
   - Review every new survivor: kill it with a real behavior test or record why it is equivalent. Do not close the branch with unexplained survivors. Reports stay ignored (`backend/mutants/`, `frontend/reports/`); commands and triage live in `docs/mutation-testing.md`.

Do not commit `.scannerwork/` or coverage artifacts. Keep generated paths excluded from Sonar (`frontend/src/api/generated/**`, `routeTree.gen.ts`, `backend/alembic/**`).
