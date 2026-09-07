---
name: frontend-image-workspace
description: >-
  Image-detail workspace for astroimage: FITS viewer canvas, inspector
  drawer, collapsible sections, HelpHint tooltips, and composable viewer
  overlays. Use when changing the image page, inspector, render/detection
  forms, metadata, source markers, or related frontend tests.
---

# Frontend image workspace

The detail route (`/image/$recordId`) is a **canvas + inspector**, not a
dashboard of cards.

## Layout

- **Canvas** — full-viewport FITS viewer (OpenSeadragon). Zoom toolbar and
  navigator stay on the image.
- **Inspector** — hamburger control; a lateral drawer with **collapsible
  sections**. The image stays visible beside the drawer.
- Do **not** add a new overlay card per endpoint or per data group.
- Do **not** dump JSON (`<pre>`) for metadata.

### Inspector sections (stable ids)

| Section | Role now | Grows into |
|---------|----------|------------|
| Vista | render form (stretch, colormap, limits, pmin/pmax, gamma) | histogram; presets/reset |
| Fuentes | detection form | presets/reset later; still one form |
| Selección | placeholder | clicked overlay item (point, extended, future kinds) and scientific metadata |
| Archivo | placeholder | grouped `/image/{id}/info` fields; FITS header last and closed |

HDU is **workspace state**, not a field inside each form. Render, histogram,
and detection share the same `hdu`. Show a selector only when
`hdus.images.length > 1`. Default `hdu` is omitted (backend picks the first
2D image HDU).

`POST /fits/metadata` is out of this workspace (no `record_id`, cannot render).

## Information density

The product will accumulate scientific metadata (per-source catalogs, later).
Keep the canvas clean:

- Markers on the image; **detail in Selección** after a click — never a
  stack of source cards on the canvas.
- `MetadataGroup` (title + labeled pairs) for instrument stats **and** for
  the selected source. New scientific fields are another group in Selección,
  not a new panel.
- Progressive disclosure: closed sections, header dump last.

## Tooltips

Almost every control and labeled value needs a short explanation.

- Use `HelpHint` (`frontend/src/components/ui/help-hint.tsx`) next to labels.
- Do not invent a second tooltip pattern. Wrap Radix `Tooltip` only there.
- `TooltipProvider` lives at the app root.
- Help copy explains meaning, not the implementation.

## Viewer overlays

The viewer accepts **composed children** inside the image stage. Point
sources are one layer (`SourceMarkers`). Extended sources and future
annotations are **sibling layers**, not extra props on `FitsImageViewer`.

- Point sources have image coordinates (`xcentroid`, `ycentroid`).
- Extended sources currently have no geometry in the API — list/count only
  until the contract adds positions.
- Selecting an overlay item fills **Selección**; it does not open a modal.

## Exclusive choice controls

Pick the control from the **size of the closed option set**, not from layout
preference:

| Options | Control |
|---------|---------|
| 1 | no control |
| 2–4 | radio group, all labels visible, one `HelpHint` on the group |
| 5+ | styled `Select` (Radix list, not native `<select>`) |
| boolean | checkbox or switch |

Use a select anyway when the list is **dynamic** (HDU indices, catalog names)
even if the current length is 2–4 — the count will change per file.

The option list of a native `<select>` is OS chrome and cannot be themed.
Use `frontend/src/components/ui/select.tsx` (Radix). Scrollbars use the same
tokens (`--border`, `--muted-foreground`, `--radius`) from `index.css`.

Today: stretch (4) and limits (2) are radios; colormap (5) uses `Select`.

## Forms (render / detection)

Contract: current values + submit. **Reset** and **named presets** (short
“what this profile is for”) will attach later without changing the inspector
layout. Do not add presets in the shell commit.

Zustand holds client/UI workspace state (drawer, selected overlay, later
`hdu` / draft params). TanStack Query remains the only server cache.
Query keys must include render/detection params when those are wired.

## Tests

- Locate controls with `data-testid` (`screen.getByTestId`).
- Route tests use a memory router.
- User events are `async` + `user-event`.
- Keep `id` / `htmlFor` / `aria-label` for accessibility; testids are extra.

## Files

```text
frontend/src/features/images/components/
  fits-image-viewer.tsx      # canvas + children slot for overlay layers
  image-inspector.tsx        # hamburger drawer + sections
  collapsible-section.tsx
  source-markers.tsx         # point layer
  source-detection-form.tsx
  render-view-form.tsx
frontend/src/features/images/render-view.ts
frontend/src/components/ui/help-hint.tsx
```

## Out of scope here

- New UI kits, Storybook, extra HTTP clients
- Upload-FITS flow until there is a persisted record
- Health endpoint in the SPA
