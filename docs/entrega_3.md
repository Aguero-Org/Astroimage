# Entrega 3 - Astroimage

En esta entrega se incorpora la carga de imágenes propias (desde archivos locales o una URL), la edición de los datos de cada imagen y la reutilización de descargas de catálogos entre regiones.

## Resumen Ejecutivo

El usuario puede incorporar imágenes que no provienen de Hubble: subir uno o varios archivos `.fits` de su computadora o indicar una URL directa al archivo. Cada imagen importada aparece en el listado con su miniatura.

Sobre cualquier imagen guardada, el usuario puede cambiar el nombre visible, la descripción y las etiquetas.

### Decisiones tomadas

- La edición toca solo los datos que guardamos de la imagen (nombre visible, descripción, etiquetas).
- La reutilización de descargas de catálogos se resuelve con PostGIS: una columna `geography(Point, 4326)`, un índice GiST y una consulta por contención del cono.
- La consulta de catálogos de una región reutiliza una descarga vigente cuando el cono pedido cae dentro del cono ya guardado, aunque el centro o el radio no coincidan exactamente.

### Desafíos técnicos encontrados

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

- Puedo importar uno o varios archivos `.fits` desde mi computadora o indicando una URL directa
- Se aceptan solo FITS con una imagen 2D; si el archivo no sirve, veo un error claro.
- Hay un límite de tamaño por archivo.
- Al terminar la importación, la imagen aparece en el listado.
- Importar la misma URL o el mismo archivo no crea una copia.
- El listado muestra la miniatura de cada imagen.
- Puedo cambiar el nombre, descripción visible de una imagen o agregar y quitar etiquetas.
