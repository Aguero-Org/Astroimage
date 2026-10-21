# astroimage frontend

Vite + React 19 SPA. Stack and commands: see the repository `astroimage/README.md` and `AGENTS.md`.

## Running without a backend

Set `VITE_API_MOCKING=true` in `.env` (or `.env.local`) to intercept all API
requests with MSW and serve mock data from `src/mocks/`. The MSW browser worker
starts before React mounts, so the SPA runs fully standalone:

```sh
VITE_API_MOCKING=true pnpm dev
```

Playwright (`pnpm test:e2e`) starts Vite on port 5174 with `VITE_API_MOCKING=true`
and `VITE_E2E=true` (it does not reuse a `pnpm dev` already on 5173). That suite
includes WCAG 2.2 AA checks (axe) on home and the image viewer with the inspector
open, in light and dark themes, including the open preset list. The FITS canvas /
OpenSeadragon navigator are excluded. Devtools overlays are hidden during e2e so
they do not count as product UI.

## Mutation testing

Stryker + Vitest covers `src/lib` and the `catalogs`/`images` features. Reports are
written to `reports/mutation/` (ignored by Git). See
[`docs/mutation-testing.md`](../docs/mutation-testing.md) for the TypeScript 7
workaround, results and survivor triage.

```sh
pnpm test:mutation:lib
pnpm test:mutation:catalogs
pnpm test:mutation:images
```
