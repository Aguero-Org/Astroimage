# Descargas de catálogos

Caché persistente de lo que VizieR devolvió para un cono. No guarda el ranking.

Una fila de `catalog_downloads` es un catálogo de esa descarga. Si el cono volvió vacío, queda una fila con `catalogue_id` vacío para no repetir la consulta.

| Campo | Uso |
| --- | --- |
| `source` | `vizier` o `simbad`. |
| `catalogue_id` | Identificador VizieR, o `simbad`. Vacío solo en el cono sin tablas. |
| `region_key` | Centro a 6 decimales, radio a 1 decimal y `row_limit`. |
| `ra_deg`, `dec_deg`, `radius_arcsec` | Región consultada. |
| `center` | Centro como `geography(Point, 4326)`, generado desde `ra_deg` y `dec_deg`. |
| `version` | Identificador compartido por las filas de una misma descarga. |
| `fetched_at` | Fecha. Vence según `CATALOG_DOWNLOAD_TTL_S` (por defecto 86400). |
| `payload` | Columnas y filas en JSON. |

Índice único: origen, catálogo, clave y `row_limit`. Índice de lectura: origen, clave y `row_limit`. Índice por `fetched_at`. Índice GiST sobre `center` para la consulta de cobertura.

## Cuándo una descarga cubre otra

Una descarga vigente responde una consulta nueva cuando:

- coincide el `source` y el `row_limit`;
- `fetched_at` está dentro de `CATALOG_DOWNLOAD_TTL_S`;
- el cono pedido queda dentro del cono guardado: la distancia entre centros más el radio pedido no supera el radio guardado. La consulta usa `ST_DWithin` sobre `center` y el índice GiST;
- ningún catálogo de la descarga alcanzó `row_limit`. Una descarga recortada por VizieR solo responde su misma `region_key`, porque no se puede afirmar que conserve todas las filas del cono menor.

El solapamiento parcial no cuenta como cobertura: el cono nuevo tiene que quedar cubierto entero. Un radio mayor, un centro corrido que no cumple la condición o un `row_limit` distinto consultan VizieR.

Cuando la descarga guardada tenía otro centro, las filas se recortan al cono pedido y la separación se recalcula desde ese centro. Un catálogo que queda sin filas en el cono nuevo no se devuelve.

La extensión `postgis` la crea la migración `20261106_0009`. El compose local y el servicio PostgreSQL de CI usan `postgis/postgis:16-3.4`.

## SIMBAD

`source` y `catalogue_id` son `simbad`. El `row_limit` es el `limit` de esa consulta (25 por defecto, 200 como máximo). VizieR sigue en 50. La cobertura exige el mismo `source` y el mismo `row_limit`.

La clave agrega el tipo de objeto al final de la clave de VizieR: `{ra}:{dec}:{radio}:{row_limit}:type={tipo}`. Sin filtro de tipo, el último tramo es `type=*`. Una descarga cubre otra consulta SIMBAD cuando cumple las reglas de arriba y el tramo `type=` es el mismo.

El radio guardado es el cono pedido a SIMBAD: la huella de la imagen, el margen de cruce y un piso de 60″. Una descarga que devolvió tantas filas como el `limit` solo responde su misma clave.

Los alias, la bibliografía y el cruce con las detecciones se calculan sobre esos objetos. La caché en memoria guarda esa respuesta ya armada. Si la descarga vigente trae otros objetos, esa respuesta no se reutiliza. `refresh` vuelve a consultar SIMBAD y reemplaza la clave de ese cono.
