# Descargas de catálogos

Caché persistente de lo que VizieR devolvió para un cono. No guarda el ranking.

Una fila de `catalog_downloads` es un catálogo de esa descarga. Si el cono volvió vacío, queda una fila con `catalogue_id` vacío para no repetir la consulta.

| Campo | Uso |
| --- | --- |
| `source` | `vizier` por ahora. SIMBAD entra después, en su card. |
| `catalogue_id` | Identificador VizieR. Vacío solo en el cono sin tablas. |
| `region_key` | Centro a 6 decimales, radio a 1 decimal y `row_limit`. |
| `ra_deg`, `dec_deg`, `radius_arcsec` | Región consultada, además de la clave. |
| `version` | Identificador compartido por las filas de una misma descarga. |
| `fetched_at` | Fecha. Vence según `CATALOG_DOWNLOAD_TTL_S` (por defecto 86400). |
| `payload` | Columnas y filas en JSON. |

Índice único: origen, catálogo, clave y `row_limit`. Índice de lectura: origen, clave y `row_limit`. Índice por `fetched_at`.

Dos consultas aciertan solo si la clave coincide. Reutilizar un cono distinto es la card de PostGIS.
