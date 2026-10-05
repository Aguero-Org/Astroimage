---
name: arch-diagrams
description: >-
  Architecture diagrams with Arc for astroimage delivery docs (entregas).
  Use when the user asks for an architecture diagram, a diagram for
  entrega 1/2/N, the US testigo flow, or anything under
  docs/architecture/. Also use when adjusting diagram style, legibility,
  or layout of an existing delivery diagram.
---

# Diagramas de arquitectura con Arc (entregas)

Fuente de verdad: `docs/architecture/<entrega>-<us>.arc.json` (datos del
diagrama) + `docs/architecture/<entrega>-<us>.svg` (render). El documento
de entrega (`docs/entrega_N.md`) embebe el SVG y agrega flujo + tabla de
componentes. Ejemplo completo: entrega 1 / US5 (`entrega1-us5.*`).

## Pipeline (siempre en este orden, desde la raíz)

```bash
npx -y @arach/arc check docs/architecture/<nombre>.arc.json
node docs/architecture/render-themed-svg.mjs docs/architecture/<nombre>.arc.json docs/architecture/<nombre>.svg <tema> <modo> transparent off
python docs/architecture/enlarge-secondary-text.py docs/architecture/<nombre>.svg
```

- `check` debe quedar sin diagnósticos antes de renderizar.
- El CLI `arc render` **no aplica temas** (ignora `_meta`; siempre sale el
  tema por defecto). Para un tema hay que usar `render-themed-svg.mjs`,
  que llama a `render_svg` del servidor MCP de Arc con `theme`/`mode`.
- Tema vigente para entregas: `command` claro, fondo transparente, sin
  grilla (brutalista minimal, colores saturados). Cambiarlo es un
  argumento; si se cambia, actualizar la nota de tema en `entrega_N.md`.

## Contenido exigido por la entrega

El diagrama toma una US testigo y muestra el flujo hasta que el resultado
queda disponible en la app:

- Componentes propios con nombres concretos del código
  (`hub/controller.py`, `ImageSearch + Results`, …), nunca tecnologías
  genéricas ("Backend", "Base de datos").
- Terceros como nodos propios (`MAST Catalog`, `MAST Download`, …).
- Separación frontend / backend / datos+terceros en tres carriles
  (grupos `frontend`, `backend`, `data`).
- En `entrega_N.md`: diagrama + flujo numerado + tabla
  Componente→Responsabilidad (incluye terceros y repositorios aunque no
  tengan flecha propia).

## Convenciones de layout (grilla)

- Nodos `size: "l"` (220×90) uniformes; columnas con `x` exacto
  compartido; filas con `y` en pitch 170 (`60 / 230 / 400 / 570`).
- Pasillos de ~140px entre carriles para que respiren las etiquetas.
- Grupos ceñidos a sus columnas; el canvas cubre grupos + margen.
- Estilos de conector fijos: `https` (blue), `internal` (zinc, sin
  label), `mast` (orange), `sql` (emerald), `s3` (sky).
- Horizontales `right→left` y verticales `bottom→top` por defecto.

## Límites de Arc (no pelear contra ellos)

- Escala tipográfica fija: títulos 12px (`l`), secundario 9px. El script
  `enlarge-secondary-text.py` lo lleva a 11.5px post-render; por eso las
  descripciones deben tener ≤30 caracteres y los nombres ≤26.
- El SVG estático renderiza solo los labels de **estilo**
  (`HTTPS`, `MAST`, …), no los `label` por conector: la semántica de cada
  flecha vive en el JSON y en el texto de `entrega_N.md`.
- `color` solo acepta colores lógicos del tema (sin hex arbitrario): el
  color final lo decide la paleta del tema elegido.
- Si un conector no puede evitar cruzar un nodo tras probar anclas,
  se elimina y se documenta el vínculo vía repositorio en la tabla
  (precedente: `TransferRunner → PostgreSQL` / `TransferRepository`).
- `_meta.themeId/mode` lo respeta el editor, no el CLI.
