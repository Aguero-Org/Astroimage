---
name: typescript
description: >-
  TypeScript types and tsconfig for the Astroimage Vite SPA. Use when
  writing types, fixing a narrowing error, or touching tsconfig. Component
  structure and server state stay in the React skills.
---

# TypeScript

The app compiler config is `frontend/tsconfig.app.json`. The Node config is `frontend/tsconfig.node.json`. Both already enable `strict`, `verbatimModuleSyntax`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `noImplicitReturns`, and `noUncheckedSideEffectImports`.

- The app resolves modules with `bundler`. Do not switch it to `nodenext`.
- Do not enable `exactOptionalPropertyTypes` or `noPropertyAccessFromIndexSignature`.
- Annotate parameters and exported signatures. Let inference type locals and returns.
- Type-only imports use `import type`.
- Boundaries return `unknown`, then narrow. Do not use `any` to get past the checker, and do not use `as` to silence an assignment error.
- Prefer a discriminated union to a bag of optional fields. Check the discriminant before reading the other fields.
- `erasableSyntaxOnly` is on. Do not add a TypeScript `enum` or `namespace`.
- A suppressed line uses `// @ts-expect-error` with a short reason, not `// @ts-ignore`.
