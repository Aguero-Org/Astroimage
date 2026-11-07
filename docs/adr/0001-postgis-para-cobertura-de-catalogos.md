# ADR 0001: PostGIS para cobertura de descargas de catálogos

- Estado: aceptado
- Fecha: 2026-11-06
- Alcance: `catalog_downloads`

## Contexto

Una descarga de VizieR se guarda por cono (centro, radio y `row_limit`). La búsqueda anterior compara la clave exacta: dos imágenes del mismo campo con el centro corrido, o el mismo campo con otro radio, vuelven a consultar VizieR aunque la región ya esté guardada.

Las consultas del proyecto son por cono. La relación entre catálogo y fuente bibliográfica es una referencia, no un grafo. Los datos viven en PostgreSQL y no hay un servicio externo que resuelva la cobertura.

## Alternativas

| Alternativa | Cono y cobertura | Relación catálogo-fuente | Operación local | Costo de migración |
| --- | --- | --- | --- | --- |
| PostgreSQL actual | Igualdad de clave; la cobertura se resuelve en código con trigonometría y sin índice espacial | Tablas y claves foráneas actuales | Un solo servicio | Nulo |
| PostGIS | `geography`, índice GiST y `ST_DWithin` en SQL | Las mismas tablas de PostgreSQL | Un solo servicio; cambia la imagen a `postgis/postgis` | Una migración y recrear la extensión en la base |
| MongoDB | Índices geoespaciales y agregaciones | Documentos embebidos o referencias manuales | Un servicio nuevo y otro driver | Migrar descargas, papers y el acceso a datos |
| Neo4J | Sin consulta de cobertura por cono | Grafo de catálogos y papers | Un servicio nuevo y otro driver | Migrar relaciones que hoy resuelven claves foráneas |

## Decisión

PostGIS dentro del PostgreSQL actual. La caché usa una columna generada `center geography(Point, 4326)`, un índice GiST y `ST_DWithin` para decidir si un cono pedido queda dentro de una descarga vigente. La regla completa está en `docs/catalog-downloads.md`.

MongoDB y Neo4J no resuelven un caso del roadmap que PostgreSQL no cubra. Agregarlas sumaría un servicio y un driver sin reemplazar el modelo relacional existente.

## Consecuencias

- La imagen local y la de CI pasan a `postgis/postgis:16-3.4`.
- La migración `20261106_0009` crea la extensión, la columna y el índice. Necesita un usuario con permiso para `CREATE EXTENSION`.
- Una descarga recortada por `row_limit` no cubre otros conos; solo responde su clave exacta.
- Cuando la descarga guardada tenía otro centro, las filas se recortan al cono pedido y la separación se recalcula.
- El volumen PostgreSQL 16 se puede reutilizar con la imagen PostGIS de la misma versión mayor; la extensión se crea en la primera migración. Si la versión de colación no coincide con la de la imagen nueva, hay que refrescarla o recrear el volumen.
