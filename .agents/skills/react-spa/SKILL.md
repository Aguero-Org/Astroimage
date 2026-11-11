---
name: react-spa
description: >-
  Where state, server data, routing, the allowed frontend stack, theming,
  and exclusive choice controls live in the Astroimage Vite SPA. Use when
  adding a component, a query, a route, client state, a form control, or a
  dependency. Effects, composition, and the image workspace have their own
  skills.
---

# React SPA

Vite + React 19 client bundle. No server components, no Next.js, no second router.

| Question | Owner |
|---|---|
| Does this need an effect? | `you-might-not-need-an-effect` |
| Boolean props, compound components, `forwardRef` | `vercel-composition-patterns` |
| Image page, inspector, glossary, overlays | `frontend-image-workspace` |
| `tsconfig` and type mechanics | `typescript` |

## Allowed stack

- Vite + React 19 + TypeScript (`strict`)
- pnpm
- shadcn/ui + Tailwind CSS v4 + Radix primitives
- TanStack Query (server state only)
- Zustand (client/UI state only)
- TanStack Router
- native `fetch` via the Orval mutator in `src/lib/api-client.ts` (`frontend/src/lib/api-client.ts`)
- Orval client generated from `backend/openapi.json`
- React Hook Form + Zod
- Biome (lint + format)
- Vitest + Testing Library + user-event + MSW
- Playwright

Do not mix TanStack Query with a global client store for server data.

## Theming

Theming is shadcn CSS variables in `frontend/src/index.css` (`:root` / `.dark`). Do not hardcode brand colors on components; use tokens (`bg-background`, `text-primary`, `border-border`, …). Five brand stops live in `frontend/src/lib/palettes.ts` as `--palette-1` (lightest) … `--palette-5` (darkest). Semantic tokens derive from those stops. Add a palette by appending an entry with five hexes; the switcher appears when there is more than one. Toggle `.dark` on `<html>` (Zustand + `localStorage`). Keep `--destructive` red.

## Exclusive choices

One value from a fixed list:

- 2–4 options → radio group (all choices visible)
- 5 or more → styled `Select` (`frontend/src/components/ui/select.tsx`, Radix). Never a native `<select>`: the option list is painted by the OS and cannot match the UI.
- 1 option → no control
- boolean on/off → checkbox or switch, not radios

Dynamic lists (HDU, catalogs) use a select even if the current count is 2–4. The count will change per file.

Scrollbars use `--scrollbar` / `--scrollbar-hover` from `frontend/src/index.css` (not `--border`: too faint on the light Apple gray).

## Where state lives

| The value | Lives in |
|---|---|
| Server data | TanStack Query. Not Zustand, not a hand-written `fetch` in an effect |
| One component | local `useState` / `useReducer` |
| A few siblings | nearest common parent |
| Shareable filter, tab, or page | TanStack Router search params |
| Rare and app-wide (theme, palette) | Zustand, narrow selector, `localStorage` |
| Frequent client/UI state read in many places | Zustand, with a narrow selector |

Colocate state. Lift it only when two siblings must share it.

Regenerate the Orval client with `pnpm generate:api` after an OpenAPI change. Do not add axios or a second client.

Query keys include every parameter that changes the response.

## Routing and bundles

- Routes are TanStack Router. Do not add React Router.
- A list that can reorder, insert, or delete uses a stable id as `key`, not the array index.
- `import.meta.env` only exposes `VITE_` variables, and those values ship in the browser bundle. Secrets stay on the API.

## What not to add

- ESLint. Lint and format are Biome. Types are `tsc`.
- React Compiler. Leave existing `useMemo` / `useCallback` alone unless the component is being rewritten for another reason.
- A virtualization library.
