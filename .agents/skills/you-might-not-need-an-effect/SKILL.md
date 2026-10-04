---
name: you-might-not-need-an-effect
description: >-
  Remove React Effects that only derive state, handle clicks, or reset
  state. Use when writing or reviewing a component that uses useEffect,
  useMemo, derived state, a key to reset state, an event handler, or
  useSyncExternalStore.
---

# You might not need an Effect

Source: https://react.dev/learn/you-might-not-need-an-effect

An Effect synchronizes the component with something outside React: a DOM widget, a subscription, the network, or the browser. If nothing outside React is involved, delete the Effect.

Ask why the code runs:

- The user did something (click, submit, drag) → event handler. If several handlers need it, call one shared function.
- The component is on screen → Effect.
- Props or state changed and the screen should show a new value → calculate it while rendering. Do not store that result in state.

## Replace the Effect

| The Effect… | Instead |
|---|---|
| Copies props or state into more state | Compute it during render |
| Recomputes something expensive | `useMemo` only when the work is actually slow. Otherwise compute during render, or move the unrelated state into a child. React Compiler may already memoize this |
| Clears all state when an id prop changes | Split the component and pass `key={id}` to the inner one |
| Adjusts one piece of state when a prop changes | Store an id and derive the object during render. Setting state during render is a last resort |
| Chains Effects that set state to trigger the next one | Compute what you can during render. Apply the rest in the event handler. State there is a snapshot: use `const next = value + 1` when the new value is needed |
| Runs once per app load | A module flag, or code in the entry module. A mount Effect runs twice in development |
| Calls `onChange` after its own state updates | Call `onChange` in the same event, or let the parent own the state |
| Fetches in the child and pushes the result up | The parent fetches and passes the data down |
| Subscribes to `window`, a store, or the browser | `useSyncExternalStore` |
| Fetches so the screen matches the current query | An Effect is allowed. Ignore stale responses in its cleanup. Prefer the app's data client over a hand-written fetch |

Do not add an Effect to transform data for rendering or to handle a user event.
