---
name: react-spa
description: >-
  Where state, server data, and routing live in the Astroimage Vite SPA.
  Use when adding a component, a query, a route, or client state. Effects,
  composition, and the image workspace have their own skills.
---

# React SPA

Vite + React 19 client bundle. No server components, no Next.js, no second router.

| Question | Owner |
|---|---|
| Does this need an effect? | `you-might-not-need-an-effect` |
| Boolean props, compound components, `forwardRef` | `vercel-composition-patterns` |
| Image page, inspector, glossary, overlays | `frontend-image-workspace` |
| `tsconfig` and type mechanics | `typescript` |

## Where state lives

| The value | Lives in |
|---|---|
| Server data | TanStack Query. Not Zustand, not a hand-written `fetch` in an effect |
| One component | local `useState` / `useReducer` |
| A few siblings | nearest common parent |
| Shareable filter, tab, or page | TanStack Router search params |
| Rare and app-wide (theme) | React context |
| Frequent client/UI state read in many places | Zustand, with a narrow selector |

Colocate state. Lift it only when two siblings must share it.

The HTTP client is the Orval mutator in `frontend/src/lib/api-client.ts`. Regenerate with `pnpm generate:api` after an OpenAPI change. Do not add axios or a second client.

Query keys include every parameter that changes the response.

## Routing and bundles

- Routes are TanStack Router. Do not add React Router.
- A list that can reorder, insert, or delete uses a stable id as `key`, not the array index.
- `import.meta.env` only exposes `VITE_` variables, and those values ship in the browser bundle. Secrets stay on the API.

## What not to add

- ESLint. Lint and format are Biome. Types are `tsc`.
- React Compiler. Leave existing `useMemo` / `useCallback` alone unless the component is being rewritten for another reason.
- A virtualization library, a new UI kit, or a new router.
