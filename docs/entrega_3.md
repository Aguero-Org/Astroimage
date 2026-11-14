# Entrega 3 - Astroimage

En esta entrega se incorpora la carga de imágenes propias (desde archivos locales o una URL), la edición de los datos de cada imagen y la reutilización de descargas de catálogos entre regiones.

## Resumen Ejecutivo

El usuario puede incorporar imágenes que no provienen de Hubble: subir uno o varios archivos `.fits` de su computadora o indicar una URL directa al archivo. Cada imagen importada aparece en el listado con su miniatura, sin necesidad de abrirla.

Sobre cualquier imagen guardada, el usuario puede cambiar el nombre visible, la descripción y las etiquetas. El archivo `.fits` y los metadatos originales se conservan.

La consulta de catálogos de una región reutiliza una descarga vigente cuando el cono pedido cae dentro del cono ya guardado, aunque el centro o el radio no coincidan exactamente.

### Decisiones tomadas

- La edición toca solo los datos que guardamos de la imagen (nombre visible, descripción, etiquetas); no modifica el `.fits` ni sus metadatos.
- Las importaciones locales y por URL no exigen proveniencia MAST; el listado muestra esos datos cuando están.
- La previsualización se genera una vez al importar, en tres resoluciones, y se guarda en el almacenamiento y en la base. El listado la sirve sin volver a renderizar.
- La reutilización de descargas de catálogos se resuelve con PostGIS: una columna `geography(Point, 4326)`, un índice GiST y una consulta por contención del cono.
- Una descarga que llegó al tope de filas responde solo su misma región.

### Desafíos técnicos encontrados

- El listado y las fichas asumían proveniencia MAST; hubo que hacerla opcional para las imágenes propias.
- Hay que generar las miniaturas en segundo plano sin demorar la respuesta de importación, y servir una imagen de reserva mientras falta.
- La reutilización por cobertura necesita reglas de radio y centro: un radio menor o un centro corrido no siempre quedan dentro de lo guardado.

---

# User Stories

## US8 - Importar y editar imágenes propias

### Actor/es

Usuario.

### Funcionalidad

Como usuario, quiero incorporar imágenes `.fits` propias y ajustar los datos con los que se guardan, para analizarlas y encontrarlas por lo que significan para mí.

Puedo subir uno o varios archivos `.fits` desde mi computadora o indicar una URL directa al archivo. La aplicación valida el archivo, lo guarda y lo suma al listado con su miniatura. Sobre cualquier imagen puedo cambiar el nombre visible, la descripción y las etiquetas. El archivo `.fits` y sus metadatos originales se conservan.

### Valor aportado

Permite analizar imágenes propias, de cualquier origen, sin depender del catálogo de Hubble, y nombrarlas y agruparlas con criterios propios.

### Criterios de aceptación

- Puedo importar uno o varios archivos `.fits` desde mi computadora.
- Puedo importar una imagen indicando una URL directa.
- Se aceptan solo FITS con una imagen 2D; si el archivo no sirve, veo un error claro.
- Hay un límite de tamaño por archivo.
- Al terminar la importación, la imagen aparece en el listado.
- Importar la misma URL o el mismo archivo no crea una copia.
- El listado muestra la miniatura de cada imagen.
- Puedo cambiar el nombre visible de una imagen.
- Puedo cambiar la descripción de una imagen.
- Puedo agregar y quitar etiquetas.
- No puedo guardar un nombre vacío ni etiquetas repetidas.
- Si un valor no es válido, veo el error y no se guarda.
- Al guardar, el listado y los datos de la imagen se actualizan sin recargar la página.
- El archivo `.fits` y los metadatos originales no cambian.
