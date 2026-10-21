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
| `catalogs/crossmatch.py` | 98 | 38 | 136 |
| `catalogs/scoring.py` | 60 | 0 | 60 |
| `fits/wcs.py` | 47 | 2 | 49 |
| `render/colormap.py` | 4 | 246 | 250 |
| `render/normalization.py` | 92 | 19 | 111 |
| `render/png.py` | 32 | 12 | 44 |
| `render/zscale.py` | 202 | 80 | 282 |
| **Total** | **535** | **397** | **932** |

Mutation score global: **57,4 %** (535/932). No hubo timeouts.

### Hallazgos iniciales

- `colormap.py` concentra 246 de los 397 supervivientes. Los tests validan forma y
  extremos de la imagen, pero no los valores intermedios de las LUT.
- `_join_identifiers` en `crossmatch.py` no está realmente ejercitado: los fixtures
  usan la columna `_2MASS`, por lo que la lista de identificadores queda vacía.
- Faltan casos límite para coordenadas parcialmente nulas, `continue` frente a
  `break`, y para el valor por defecto de `probability_power`.
- `normalization.py` no comprueba el `dtype` del retorno temprano para una imagen
  completamente NaN ni la fórmula exacta del stretch logarítmico.
- El test de `limits="zscale"` no distingue esa rama de la rama de percentiles.
- Varios supervivientes de `_fit_line`, del `frame=None` de WCS y del cambio
  `format="png"` a `"PNG"` parecen equivalentes; deben revisarse antes de añadir
  tests o exclusiones.

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

### Resultado inicial

`src/lib` (8 archivos, 150 mutantes):

| Archivo | Killed | Survived | No coverage | Total |
| --- | ---: | ---: | ---: | ---: |
| `api-client.ts` | 39 | 14 | 2 | 55 |
| `api-response.ts` | 4 | 2 | 0 | 6 |
| `palettes.ts` | 4 | 2 | 6 | 12 |
| `polled-job.ts` | 13 | 2 | 0 | 15 |
| `query-client.ts` | 5 | 0 | 0 | 5 |
| `theme-store.ts` | 9 | 10 | 12 | 31 |
| `theme.ts` | 5 | 2 | 18 | 25 |
| `utils.ts` | 1 | 0 | 0 | 1 |
| **Total** | **80** | **32** | **38** | **150** |

Mutation score total: **53,33 %**; sobre código cubierto: **71,43 %**.

Muestra de features (2 archivos, 337 mutantes):

| Archivo | Killed | Survived | No coverage | Total |
| --- | ---: | ---: | ---: | ---: |
| `catalogs/catalog-recommendations.ts` | 163 | 94 | 12 | 269 |
| `images/image-title.ts` | 33 | 26 | 9 | 68 |
| **Total** | **196** | **120** | **21** | **337** |

Mutation score total: **58,16 %**; sobre código cubierto: **62,03 %**.

### Hallazgos iniciales

- `theme.ts` y `theme-store.ts` tienen muchos mutantes sin cobertura: no hay tests
  dedicados para resolución, persistencia y toggle del tema.
- En `api-client.ts` sobreviven defaults, claves de `localStorage`, mensajes de
  `ApiError` y la rama que añade `Content-Type: application/json`.
- `image-title.ts` sobrevive a la mayoría de variaciones del regex UUID; conviene
  añadir casos válidos e inválidos, no solo un caso feliz.
- `polled-job.ts` sobrevive a mutaciones de `isFetching`; el estado combinado no se
  comprueba con suficiente precisión.
- La muestra de features no es la feature completa: `test:mutation:catalogs` e
  `test:mutation:images` siguen pendientes como corridas de referencia.

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
