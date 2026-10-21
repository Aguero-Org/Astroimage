# Mutation testing

Guía de las corridas de `mutmut` (backend) y Stryker + Vitest (frontend). Mutation
testing no forma parte todavía de la CI obligatoria: se usa como análisis periódico
para detectar tests que pasan sin comprobar el comportamiento.

Última corrida de referencia: **2026-10-21**.

## Alcance

- Backend: siete módulos de cálculo y render, con sus tests unitarios actuales.
- Frontend: `src/lib` completo y una muestra de `catalogs` e `images`.
- Los reportes y la caché son artefactos locales; no se versionan.

## Cierre de branch

Mutation testing es un **gate local de cierre**, todavía no un job de CI. Antes de
considerar terminada una branch que toque código backend o frontend:

1. Ejecutar la suite de mutación del stack afectado.
2. Revisar los supervivientes nuevos.
3. Matarlos con un test de comportamiento real o documentar por qué son equivalentes.

Comandos mínimos:

```bash
# Backend (incremental si existe backend/mutants/)
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut run --max-children 2"

# Frontend
cd frontend
pnpm test:mutation:lib        # cambios en src/lib
pnpm test:mutation:catalogs   # cambios en catalogs
pnpm test:mutation:images     # cambios en images
```

Si el cambio es transversal a render/números o a varias features, ejecutar el alcance
completo configurado (`pnpm test:mutation`). Una branch que solo toca documentación no
necesita esta corrida.

## Backend (`mutmut`)

### Requisitos

`mutmut` necesita `fork`, por lo que no se ejecuta contra el `.venv` de Windows.
En Windows se usa WSL. No hace falta copiar el repositorio: se puede trabajar sobre
el mount de WSL (`/mnt/d/...`) y mantener el entorno virtual fuera del proyecto.

```bash
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv sync --frozen --all-groups"
```

Si `uv` está en el `PATH` de la distro, se puede reemplazar `~/.local/bin/uv` por `uv`.

### Configuración

La sección `[tool.mutmut]` de `backend/pyproject.toml` define:

- `source_paths = ["src"]`.
- `only_mutate`: `catalogs/crossmatch.py`, `catalogs/scoring.py`, `fits/wcs.py`,
  `render/colormap.py`, `render/normalization.py`, `render/png.py` y
  `render/zscale.py`.
- Tests seleccionados: `tests/unit/catalogs`, `tests/unit/fits/test_wcs.py` y
  `tests/unit/render`, sin cobertura (`--no-cov`).
- `timeout_multiplier = 30.0` y `timeout_constant = 30.0`.

El timeout es alto a propósito. En WSL el arranque de pytest para cada mutante tarda
alrededor de 8 segundos; con un límite de 5 segundos se producían timeouts falsos.

### Ejecución

```bash
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut run --max-children 2"
```

La corrida completa tarda aproximadamente 25–30 minutos con dos workers. `mutmut`
guarda el progreso en `backend/mutants/`; una nueva ejecución solo repite los
mutantes pendientes o los de funciones cuyo código cambió.

### Reportes

```bash
# Lista de mutantes que sobreviven
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut results"

# Ver el diff de un mutante
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut show <mutante>"

# Estadísticas agregadas para un tablero externo
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut export-cicd-stats"
```

`export-cicd-stats` escribe `backend/mutants/mutmut-cicd-stats.json`. También existen
`mutmut browse` y `mutmut tests-for-mutant` para inspección interactiva. Todo
`backend/mutants/` está ignorado por Git.

### Resultado inicial

| Archivo | Killed | Survived | Total |
| --- | ---: | ---: | ---: |
| `catalogs/crossmatch.py` | 127 | 9 | 136 |
| `catalogs/scoring.py` | 60 | 0 | 60 |
| `fits/wcs.py` | 47 | 2 | 49 |
| `render/colormap.py` | 225 | 25 | 250 |
| `render/normalization.py` | 107 | 4 | 111 |
| `render/png.py` | 39 | 5 | 44 |
| `render/zscale.py` | 263 | 19 | 282 |
| **Total** | **868** | **64** | **932** |

Mutation score global: **93,1 %** (868/932). No hubo timeouts. La tabla combina la
corrida inicial con las corridas dirigidas posteriores de `crossmatch`,
`normalization`, `zscale`, `colormap` y `png`; `scoring` y `wcs` siguen en su estado
inicial.

### Hallazgos iniciales

- `colormap.py` concentraba 246 de los 292 supervivientes iniciales: los tests
  validaban forma y extremos, pero no los valores intermedios de las LUT. La corrida
  dirigida posterior los redujo a 25 equivalentes (ver abajo).
- `crossmatch.py` quedó cubierto con identificadores visibles/ocultos, coordenadas
  parcialmente nulas, filas inválidas y límites de radio/potencia: 127/136 killed.
  Los 9 restantes son equivalentes (frames por defecto ICRS, `strict` redundante,
  cap inobservable de 2 y `or True` en unmatched).
- `normalization.py` quedó en 107/111: se cubren fórmulas exactas, `dtype`, gamma,
  clipping, zscale frente a percentiles y error de stretch. Los 4 supervivientes
  son cambios de `dtype`/asignación sin efecto observable para arrays numéricos.
- `zscale.py` quedó en 263/282. Se cubren sampler, sigma, ventana, mediana par,
  crecimiento y límites de referencia; los 19 restantes son en su mayoría
  equivalentes de convergencia, `dtype` o igualdad exacta en el umbral.
- Varios supervivientes de `_fit_line` y del `frame=None` de WCS parecen
  equivalentes; deben revisarse antes de añadir tests o exclusiones. El cambio
  `format="png"` a `"PNG"` quedó confirmado como equivalente en la corrida dirigida
  de `png`.

### Corrida dirigida render (`normalization` + `zscale`)

- 393 mutantes: **370 killed**, **23 survived**, 0 timeouts.
- `normalization.py`: 4 supervivientes (`x_normalize_to_uint8__mutmut_3,5,27,29`).
  Son cambios de `dtype` de entrada, `np.all(None)` y asignación de `None` a píxeles
  no finitos; el resultado observable no cambia para arrays numéricos.
- `zscale.py`: 19 supervivientes. `_sample_pixels` `50,52` son `dtype`; `_compute_sigma`
  `3,7,14,16` son ramas inalcanzables tras el early return; `_fit_line`
  `10-13,18,20,29` son escalas/órdenes equivalentes, `34,35` solo cambian la
  convergencia del loop y `77,79` solo difieren si un residuo cae exactamente en el
  umbral; `zscale_bounds` `3,5` son `dtype` de entrada.
- La verificación de `_fit_line` `34,35,77,79` se hizo con 10.000 arrays aleatorios
  sin diferencias observables; se aceptan como equivalentes de convergencia/borde.

### Corrida dirigida render (`colormap` + `png`)

- 294 mutantes: **264 killed**, **30 survived**, 0 timeouts.
- Se añadieron tests de referencia de las cinco LUT (`grey`, `inverse`, `heat`,
  `rainbow`, `cube_helix`) contra sus fórmulas completas, 256 filas, `dtype` y el
  escalado de `_build_luts`; también el mapeo de todos los índices en
  `apply_colormap`.
- `colormap.py`: 25 supervivientes, todos equivalentes.
  - `_heat_lut` `14,23,27,36`: límites superior de `np.clip` a `None`/`2.0`; con
    `intensity` en [0,1] el clip superior es redundante.
  - `_rainbow_lut` `17,21,47-54,70-73,75,82,91,92`: `astype(None)`, `% 7`,
    condiciones duplicadas/inalcanzables (`==5`, `!=5`, `==6`) y valores del
    segmento que nunca se alcanza; el array resultante no cambia.
  - `_cube_helix_lut` `71,72,77`: `np.clip` inferior/superior; los canales
    generados ya están en [0,1].
- `png.py`: 5 supervivientes equivalentes. `mode=None` y omitir `mode` dejan que
  Pillow infiera `L`/`RGB` desde el array ya convertido a `uint8`; `format="png"` es
  equivalente a `"PNG"` (Pillow normaliza el nombre del formato).

## Frontend (Stryker + Vitest)

### Configuración

`frontend/stryker.config.json` usa:

- Mutación de `src/lib/**/*.ts`, `src/features/catalogs/**/*.{ts,tsx}` y
  `src/features/images/**/*.{ts,tsx}`, excluyendo tests.
- Runner `vitest` con `vite.config.ts`.
- Reportes HTML y JSON en `frontend/reports/mutation/`.
- Umbrales 80/60, pero `break: null`: la corrida reporta sin romper el comando.

El plugin se declara explícitamente en `plugins` porque con el layout aislado de
pnpm la autodetección por glob de Stryker no encontraba
`@stryker-mutator/vitest-runner`.

TypeScript 7 todavía no es compatible con el parser de Stryker 10. El workaround
está en `frontend/pnpm-workspace.yaml`: la extensión de paquete inyecta
`@typescript/typescript6` solo dentro de `@stryker-mutator/core`. Se debe eliminar
cuando Stryker soporte TypeScript 7; seguimiento en
<https://github.com/stryker-mutator/stryker-js/issues/6110>.

### Ejecución

```bash
cd frontend

pnpm test:mutation:lib        # src/lib
pnpm test:mutation:catalogs   # toda la feature catalogs
pnpm test:mutation:images     # toda la feature images
pnpm test:mutation            # alcance completo configurado
```

Los scripts de feature pueden tardar mucho más que el subset de `src/lib`. Para
iterar sobre un archivo concreto:

```bash
pnpm exec stryker run --mutate "src/features/catalogs/catalog-recommendations.ts"
```

Cada corrida sobrescribe `frontend/reports/mutation/index.html` y
`frontend/reports/mutation/mutation.json`; el reporte corresponderá siempre al
último comando ejecutado. El reporte actual en el repo local es el de la muestra de
features.

### Resultado actual

`src/lib` (8 archivos, 150 mutantes):

| Archivo | Killed | Survived | No coverage | Total |
| --- | ---: | ---: | ---: | ---: |
| `api-client.ts` | 54 | 1 | 0 | 55 |
| `api-response.ts` | 6 | 0 | 0 | 6 |
| `palettes.ts` | 11 | 1 | 0 | 12 |
| `polled-job.ts` | 15 | 0 | 0 | 15 |
| `query-client.ts` | 5 | 0 | 0 | 5 |
| `theme-store.ts` | 26 | 3 | 2 | 31 |
| `theme.ts` | 25 | 0 | 0 | 25 |
| `utils.ts` | 1 | 0 | 0 | 1 |
| **Total** | **143** | **5** | **2** | **150** |

Mutation score total: **95,33 %**; sobre código cubierto: **96,62 %**.

Muestra de features (2 archivos, 337 mutantes):

| Archivo | Killed | Survived | No coverage | Total |
| --- | ---: | ---: | ---: | ---: |
| `catalogs/catalog-recommendations.ts` | 260 | 9 | 0 | 269 |
| `images/image-title.ts` | 68 | 0 | 0 | 68 |
| **Total** | **328** | **9** | **0** | **337** |

Mutation score total: **97,33 %**; sobre código cubierto: **97,33 %**.

Los 7 supervivientes de `src/lib` (5 survived + 2 no coverage) y los 9 de
`catalog-recommendations.ts` se revisaron y son equivalentes:

- `api-client.ts`: el fallback de `content-type` a `"Stryker was here!"` solo se usa
  en `.includes("json")`; sin cabecera y con cuerpo no JSON la rama útil es el Blob.
- `palettes.ts`: `true && value in PALETTES` coincide con `value !== null`; `null in
  PALETTES` devuelve `false` sin lanzar.
- `theme-store.ts`: las ramas `typeof document === "undefined"` no se alcanzan en el
  SPA, y `set({})` no altera nada mientras exista una sola paleta.
- `catalog-recommendations.ts`: `title && true` y `title.length >= 0` no cambian el
  resultado porque `title` ya viene de `trim()`; `detail` siempre es no vacío; el
  early return de query vacía equivale a `includes("")`; `boundary >= 0` es
  inalcanzable cuando el texto ya está trimmeado.

Se añadieron tests de tema, `api-client`, `api-response`, `polled-job`, títulos de
imagen (UUID exactos, hashes finales, extensiones), y recomendaciones de catálogo
(columnas, región, DOI/ReadMe, filtros, truncado y enlaces). `image-title.ts` queda
al 100 %.

## Cómo revisar un superviviente

1. Abrir el diff en el reporte o con `mutmut show <mutante>`.
2. Reproducirlo con el test más pequeño que lo cubra.
3. Clasificarlo:
   - **Equivalente**: el mutante produce el mismo comportamiento observable. No se
     añade un test artificial; si se excluye, debe quedar justificado.
   - **Hueco de test**: falta una aserción o un caso límite. Añadir el test en el
     módulo que corresponde.
   - **Comportamiento no cubierto**: el test no se ejecuta para ese código. Añadir
     cobertura antes de perseguir el score.
4. No bajar umbrales ni desactivar mutadores para hacer subir el número.

## Limitaciones

- `mutmut` no corre de forma nativa en Windows; requiere WSL.
- Los mutation scores no son comparables con el coverage porcentual.
- Algunos mutantes son equivalentes; el score no debe interpretarse como porcentaje
  exacto de bugs detectables.
- La corrida frontend de referencia cubre `src/lib` y solo dos archivos de features.
- Las corridas completas de `catalogs` e `images` son costosas y no se ejecutaron
  todavía.
- No hay job de CI ni Quality Gate de mutation testing. `break: null` y la ausencia
  de un paso en GitHub Actions son intencionales en esta etapa.
