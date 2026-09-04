# astroimage frontend

Vite + React 19 SPA. Stack and commands: see the repository `astroimage/README.md` and `AGENTS.md`.

## Running without a backend

Set `VITE_API_MOCKING=true` in `.env` (or `.env.local`) to intercept all API
requests with MSW and serve mock data from `src/mocks/`. The MSW browser worker
starts before React mounts, so the SPA runs fully standalone:

```sh
VITE_API_MOCKING=true pnpm dev
```
