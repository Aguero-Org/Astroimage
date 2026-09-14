# PoC - Astroimage

## Resumen Ejecutivo

### Qué se agregó/modificó en esta iteración

Durante la PoC (Proof of Concept) de **Astroimage** se construyó el núcleo mínimo para validar que un usuario no experto puede **buscar un objeto celeste, obtener un FITS real, verlo y detectar fuentes** sin instalar software astronómico de escritorio.

En esta etapa se implementaron y validaron:

- **Página inicial** con buscador por nombre de objeto (por ejemplo `M31`, `NGC 1300`) y listado de imágenes ya ingestadas.
- **Ingestión de FITS** desde catálogos públicos (astroquery / SkyView) hacia almacenamiento local.
- **Persistencia híbrida**: PostgreSQL para metadatos e identificadores; MinIO para el binario FITS (archivos de decenas de MB a más de 1 GB).
- **Render configurable** del array FITS a PNG (stretch lineal / sqrt / log / asinh, límites percentil o zscale, mapas de color).
- **Visor interactivo** (pan, zoom) con inspector lateral (Vista, Fuentes, Selección, Archivo).
- **Detección de fuentes puntuales** (`photutils` / DAOStarFinder) y marcadores sobre la imagen.
- **Extracción de metadatos** de cabeceras FITS (HDU, WCS cuando existe).
- **Datos de prueba** (seed dump/load) y **observabilidad** (health, métricas Prometheus, logs JSON, traces OTLP opcionales).
- **Identidad visual** (logo / isotipo) y **stack + licencia** definidos.

### Decisiones tomadas

#### Empezar por lo que más podía fallar

Se priorizó lo que había que demostrar: buscar un objeto por nombre, ver la imagen y marcar fuentes. Si eso no funcionaba, el resto del producto no tenía sentido.

#### Guardar la ficha por un lado y el archivo por otro

Las imágenes astronómicas ocupan mucho. Se decidió guardar en un lado la ficha (nombre, identificador, datos del archivo) y en otro el archivo en sí. Así se puede listar y reabrir imágenes sin volver a bajarlas, y sin que el tamaño del archivo trabe el resto de la aplicación.

#### Bajar la imagen por nombre de objeto, no recorriendo a mano el sitio de Hubble

Al principio la idea era entrar al sitio del Hubble y bajar el archivo desde ahí. En la PoC se eligió un catálogo público que, con el mismo nombre que escribe el usuario (`M31`, `NGC 1300`, …), entrega una imagen usable. El resultado para quien usa la app es el mismo; queda pendiente, para más adelante, dejar elegir cuál imagen usar cuando hay varias misiones del mismo objeto.

#### La imagen es el centro; los controles no tapan el resto

Se evitó un recorrido de varias pantallas. La persona se queda mirando la imagen; a un costado, cuando lo necesita, abre un panel con vista, fuentes, selección y datos del archivo. Los puntos detectados se dibujan encima de la imagen, para poder sumar otros tipos de marcas después sin rediseñar la pantalla.

#### Control de calidad desde el principio

Aunque el usuario no lo ve, se acordó revisar el código de forma automática desde el principio (pruebas, formato, calidad). La PoC tiene que poder seguir creciendo en las próximas entregas, no rehacerse.

### Desafíos técnicos encontrados

- Convertir un array científico (dinámica enorme, NaNs, HDUs múltiples) en una imagen que un humano pueda interpretar (stretch, zscale, colormaps).
- Detectar fuentes puntuales sin inundar el visor: umbrales (FWHM, sigma, SNR, distancia mínima, tope de fuentes).
- Archivos FITS grandes: no pasar el binario por PostgreSQL; servir un PNG renderizado, no el FITS crudo, al browser.

---

# User Stories

## US1 - Página inicial y búsqueda de objeto celeste

### Actor/es

- Usuario (estudiante o aficionado)

### Funcionalidad

Como usuario, quiero una página inicial con un buscador por nombre de objeto para encontrar o descargar una imagen FITS asociada.

### Valor aportado

Es el punto de entrada: no hay que saber URLs de misiones ni manejar archivos a mano para empezar a explorar.

### Criterios de aceptación

- Al abrir la aplicación veo el logo, el título Astroimage y un campo de búsqueda.
- Puedo buscar por nombre conocido (`M31`, `NGC 1300`, etc.).
- Si el objeto no está en el almacenamiento local, el sistema intenta ingestirlo desde el catálogo configurado y aparece en el listado.
- Si la búsqueda falla (objeto inexistente o error de red del catálogo), veo un mensaje de error usable.
- El listado muestra las imágenes disponibles (con o sin filtro de búsqueda) y puedo elegir una.

---

## US2 - Visualizar un FITS de forma interactiva

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero abrir una imagen de la lista y verla renderizada, con pan/zoom, sin instalar un visor FITS de escritorio.

### Valor aportado

Un FITS científico se puede mostrar en el browser de forma comprensible.

### Criterios de aceptación

- Al elegir una imagen navego a `/image/{id}`.
- Veo un PNG generado a partir del HDU de imagen (no el binario FITS crudo).
- Puedo hacer pan y zoom.
- Puedo cambiar stretch (lineal, sqrt, log, asinh), límites (percentiles / zscale) y mapa de color; la vista se actualiza.
- Si hay varios HDU de imagen, puedo elegir cuál ver.
- Los controles viven en el inspector (sección Vista), no en otra página.

---

## US3 - Detectar y ver fuentes puntuales sobre la imagen

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero detectar fuentes puntuales (estrellas / objetos compactos) y verlas marcadas sobre el FITS, con parámetros ajustables.

### Valor aportado

El usuario relaciona píxeles con candidatos a fuentes.

### Criterios de aceptación

- En el inspector, sección Fuentes, puedo lanzar una detección con parámetros (FWHM, sigma, SNR mínimo, distancia mínima, máximo de fuentes, etc.).
- Las fuentes aparecen como marcadores alineados con el zoom/pan del visor.
- Puedo seleccionar una fuente y ver sus datos en la sección Selección.
- Si no hay detecciones o falla el HDU, el estado se comunica (vacío / error), no una pantalla en blanco.
---

## US4 - Consultar metadatos del archivo FITS

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero ver información del archivo (cabeceras, HDU, identificador) junto a la imagen para entender qué estoy mirando.

### Valor aportado

Permite al usuario conocer los metadatos del archivo FITS sin necesidad de un software de terceros.

### Criterios de aceptación

- En el inspector, sección Archivo, veo metadatos extraídos del FITS.
- El identificador del registro coincide con el de la URL y el listado.
- Un FITS inválido o sin HDU de imagen 2D se rechaza con un error claro al ingestirlo o al pedirlo.

---

## T1 - Persistencia de FITS (PostgreSQL + MinIO)

### Objetivo

Guardar metadatos en PostgreSQL y el binario en MinIO, vinculados por un id.

### Valor aportado

Permite reabrir imágenes sin volver a bajarlas del catálogo y soporta archivos grandes.

### Resultado esperado

- Cada FITS ingestado tiene un registro con id y metadatos.
- El objeto existe en el bucket MinIO.
- Listar / buscar / renderizar / detectar usan ese id.
- Hay un mecanismo de seed (dump/load) para demos y tests.

---

## T2 - Plataforma de desarrollo y observabilidad

### Objetivo

Dejar un entorno reproducible (Compose, CI, health, métricas) para las siguientes entregas.

### Resultado esperado

- `docker compose up` levanta API, frontend, PostgreSQL y MinIO.
- `/health` y `/metrics` responden.
- Stack de monitoring (Prometheus, Grafana, Loki, Tempo) es opcional y externo a la imagen de la app.
- CI corre linters y tests en backend y frontend.