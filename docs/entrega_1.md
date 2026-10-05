# Entrega 1 - Astroimage

En esta entrega se incorporan dos capacidades principales: buscar y obtener imágenes de Hubble, y explorar y analizar una imagen.

## Resumen Ejecutivo

El usuario puede buscar imágenes disponibles de Hubble, revisar los resultados, seleccionar una imagen y descargarla. La descarga informa su progreso y puede retomarse si fue interrumpida.

Una vez obtenida la imagen, el usuario puede visualizarla y analizar las fuentes presentes. Puede detectar fuentes puntuales y extendidas, ajustar los parámetros de detección y contrastar los resultados con Gaia. También puede consultar el histograma y el significado de los parámetros mediante el glosario.

### Decisiones tomadas

- La descarga se realiza por partes para poder mostrar el progreso y retomar una transferencia interrumpida.
- Las partes temporales se eliminan una vez que la imagen queda guardada.
- Los parámetros de detección pueden ajustarse según las características de cada imagen.
- Se mide el FWHM de la imagen para obtener información que permita recomendar parámetros de detección.
- Cuando no es posible realizar una medición confiable, no se genera una recomendación.
- La medición se realiza cuando el usuario la solicita.
- Las fuentes puntuales y extendidas se muestran como capas independientes sobre la imagen.
- Los errores producidos durante las operaciones se traducen en un único punto antes de llegar al cliente.

### Desafíos técnicos encontrados

- El servicio de Hubble no siempre informa inicialmente el tamaño total del archivo, por lo que fue necesario contemplar la descarga por partes.
- La verificación con Gaia puede requerir tiempo, por lo que se resuelve de forma asíncrona.
- Fue necesario distinguir entre una búsqueda sin detecciones y un error de configuración del detector.
- Se detectaron diferencias entre el contrato OpenAPI y el comportamiento real de algunos parámetros opcionales.

---

# User Stories

## US5 - Buscar y obtener imágenes

### Actor/es

Usuario.

### Funcionalidad

Como usuario, quiero buscar y seleccionar una imagen de Hubble para incorporarla a la aplicación y poder analizarla.

Puedo buscar un objeto celeste y consultar las imágenes disponibles. Puedo recorrer los resultados, ordenarlos y seleccionar la imagen que quiero obtener.

Al iniciar la descarga puedo consultar su progreso y cancelarla. Si la descarga se interrumpe, puedo retomarla posteriormente.

Cuando la descarga termina, la imagen queda disponible para ser visualizada y analizada.

### Valor aportado

Permite elegir la imagen que se quiere estudiar y obtenerla sin tener que gestionar manualmente la descarga desde el servicio externo.

### Criterios de aceptación

- Puedo buscar imágenes de Hubble indicando un objeto celeste.
- Puedo consultar y recorrer los resultados.
- Puedo ordenar los resultados.
- Puedo seleccionar una imagen para descargar.
- Puedo consultar el progreso de la descarga.
- Puedo cancelar una descarga.
- Una descarga interrumpida puede retomarse.
- Una descarga completada deja la imagen disponible para su análisis.

---

## US6 - Explorar y analizar imágenes

### Actor/es

Usuario.

### Funcionalidad

Como usuario, quiero explorar una imagen y analizar las fuentes que contiene.

Puedo visualizar una imagen y explorarla mediante zoom y desplazamiento. Puedo detectar fuentes puntuales y extendidas y ajustar los parámetros utilizados para la detección.

La aplicación puede recomendar parámetros a partir de las características de la imagen. También puedo consultar el histograma y acceder a información sobre los parámetros mediante el glosario.

Las detecciones obtenidas pueden contrastarse con información del catálogo Gaia para determinar su correspondencia con objetos registrados en dicho catálogo.

### Valor aportado

Permite analizar una imagen obtenida, identificar las fuentes presentes y contrastar los resultados con información astronómica externa.

### Criterios de aceptación

- Puedo visualizar una imagen descargada.
- Puedo explorar la imagen mediante zoom y desplazamiento.
- Puedo detectar fuentes puntuales.
- Puedo detectar fuentes extendidas.
- Puedo modificar los parámetros utilizados para la detección.
- Puedo obtener una recomendación de parámetros basada en las características de la imagen.
- Puedo consultar el histograma de la imagen.
- Puedo consultar información sobre los parámetros utilizados.
- Puedo contrastar las detecciones con el catálogo Gaia.
- Puedo consultar la correspondencia encontrada para las detecciones.

---

# Diagrama de arquitectura

El diagrama de arquitectura se realizará tomando como user story testigo **US5 - Buscar y obtener imágenes**.

> **PLACEHOLDER — DIAGRAMA DE ARQUITECTURA**
>
> El diagrama debe mostrar cómo se resuelve técnicamente la US5, incluyendo:
>
> - Los componentes propios que participan en el flujo.
> - Los componentes de terceros involucrados.
> - La separación entre frontend y backend.
> - Las relaciones y comunicaciones entre los componentes.
> - La responsabilidad de cada componente.
> - Los nombres concretos de los componentes, evitando representar únicamente tecnologías genéricas como "Frontend", "Backend" o "Base de datos".
>
> Debe representar el flujo de la búsqueda, selección y descarga de una imagen de Hubble hasta que la imagen queda disponible en la aplicación.

### Componentes

> **PLACEHOLDER — COMPONENTES DEL DIAGRAMA**
>
> Para cada componente identificado en el diagrama se debe indicar brevemente su responsabilidad.

