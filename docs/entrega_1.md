# Entrega 1 - Astroimage

Documento de la primera entrega posterior a la PoC. La PoC ([[POC-documentacion]]) validó el
núcleo mínimo: buscar un objeto, bajarlo, verlo y detectarle fuentes puntuales. Esta entrega
deja de adivinar: el usuario elige qué imagen bajar, la descarga se puede retomar, y los
parámetros de detección salen de medir la imagen en lugar de ajustarlos a ciegas.

La numeración de User Stories y Tareas continúa la de la PoC (`US1`–`US4`, `T1`–`T2`).

Las historias y las tareas están agrupadas en cuatro bloques: **descarga de imágenes**,
**detección de fuentes**, **verificación con Gaia** y **glosario y ayudas contextuales**.

---

## Resumen Ejecutivo

### Qué se agregó en esta entrega

- **Búsqueda paginada en Hubble** (`GET /image/search`) en lugar de quedarse con el primer
  producto science de la primera observación: se listan candidatos y el usuario elige cuál bajar.
- **Transferencias reanudables** (`GET /image/transfers/{transfer_id}`, `/cancel`, `/resume`): la
  descarga reporta progreso real, se puede cancelar y retomar, y aguanta archivos de cientos de MB.
- **Borrado de imágenes** ya guardadas (`DELETE /image/{record_id}`).
- **Catálogo compartido** entre imágenes almacenadas y candidatos de Hubble, con el mismo
  formato de tabla en vez de dos listados distintos.
- **Detección de fuentes extendidas** además de las puntuales: nebulosa, filamentos y resto de
  emisión se detectan con su propio grupo de parámetros (`ext_sigma`, `ext_smooth_sigma`,
  `ext_min_area`, `ext_max_area`, `ext_closing_iterations`, `ext_opening_iterations`,
  `ext_min_score`, `ext_max_sources`) y con sus propios marcadores.
- **Preset recomendado medido en la imagen** (`GET /image/{record_id}/sources/bestPreset`): el
  backend mide el FWHM real de las fuentes de esa imagen y reescala los umbrales a partir de esa
  medida. Incluye la evidencia de la medición para que el usuario sepa en qué se basing.
- **Verificación contra Gaia DR4** (`GET /image/{record_id}/sources/gaia` y
  `/sources/gaia/jobs/{job_id}`): cruza las detecciones con el catálogo para confirmar que lo
  marcado es una estrella real y no ruido.
- **Histograma de la imagen** (`GET /image/{record_id}/histogram`) para elegir límites de
  estirado con criterio en lugar de a ojo.
- **Glosario en la app** (`/glossary`) con ~50 conceptos, enlazado desde los rótulos del
  inspector mediante tooltips, para que ningún parámetro quede sin explicar.
- **Tema claro/oscuro** con cinco paletas de marca intercambiables.
- **Copiar valores del inspector** (un campo o un grupo entero) con confirmación por toast.

### Decisiones tomadas

#### Bajar en partes, no de un tirón

Un FITS de Hubble puede pesar cientos de MB. La descarga se corta en trozos que se guardan como
objetos sueltos y se leen y ensamblan al final. Eso habilita mostrar progreso real, cancelar y
retomar, y evita que un corte de conexión tire el trabajo entero.

#### Los trozos se borran cuando la transferencia termina

Los trozos solo hacen falta hasta que el archivo queda guardado como imagen. Mantenerlos
duplicaba el espacio usado en MinIO sin ningún beneficio, así que el runner los purga al
completar la transferencia. La purga se hace en segundo plano: si falla, loguea una advertencia en
vez de levantar una excepción, para que un problema de storage no convierta una imagen ya guardada
en una transferencia fallida.

#### Medir el FWHM en la imagen en vez de adivinarlo

El FWHM que funciona en una imagen borrosa es demasiado chico para una nítida, y al revés: con
los valores por defecto una nebulosa se come vecinas y una imagen abierta no detecta casi nada.
En lugar de ajustar a mano imagen por imagen, el backend toma momentos de segundo de las fuentes
puntuales ya detectadas y agranda de forma iterativa la ventana de medición (el "stamp") hasta que
cubre 4.5σ. La ventana tiene que refinarse porque un tamaño fijo de 6 píxeles truncaba los núcleos
anchos y devolvía un FWHM subestimado.

#### Lo que la medición no cambia, no se toca

La recomendación devuelve solo los umbrales que dependen del PSF (fwhm, min_distance,
visual_area_radius, smooth_sigma, min_area) y arrastra intactos los que dependen del gusto o del
instrumento (sigma de fondo, SNR mínimo, score, pesos visuales, topes de fuentes). Cambiar de
imagen no debería resetearle a la persona los knobs que eligió a mano.

#### Si no se puede medir, no inventar

Si la imagen tiene pocas fuentes limpias para medir, la respuesta vuelve con los valores que el
usuario ya tenía y lo dice en la evidencia, en vez de devolver un número sin respaldo.

#### La medición es a pedido, no al abrir la imagen

Medir implica leer la imagen. Pedirlo automáticamente en cada HDU que se abre sería tirar cómputo
sin que el usuario lo haya pedido, así que la recomendación se ofrece como un botón en la sección
Fuentes del inspector.

#### Las capas del visor se componen como hermanos

Los marcadores de fuentes puntuales y los de fuentes extendidas se dibujan como capas hermanas
sobre el canvas, no cableados adentro del visor. Sumar un tercer tipo de marca después no debería
requerir rediseñar el visor.

#### Un error se traduce en un solo lugar

Cada controller envolvía sus llamadas en `try/except` para armar su `HTTPException`, lo que
distribuía la semántica HTTP por cuatro features. Ahora `shared/errors.py` es el dueño: las
subclases de `AppError` declaran su propio status, `LookupError` / `ValueError` / `OSError`
conservan sus 404 / 400 / 400 anteriores, y cualquier otra excepción se vuelve un 500 genérico
que no filtra el mensaje original al cliente. Un test de arquitectura falla si un controller
vuelve a importar `HTTPException`.

### Desafíos técnicos encontrados

- Bajar un producto science real de Hubble con progreso honesto: el tamaño total no siempre viene
  en el HEAD, así que el rango se lee por partes hasta que el servidor deja de devolver bytes.
- Que la verificación con Gaia no bloquee el request cuando hay miles de detecciones y la consulta
  al archivo tarda: se resuelve como un job con su propio endpoint de consulta.
- No confundir "el detector no encontró nada" con "el detector está mal configurado": la evidencia
  de la medición viaja junto con la respuesta.
- Los parámetros de detección son todos opcionales en el contrato OpenAPI (salen de un modelo de
  query), así que el frontend tiene que tratar `undefined` como "no tocar" y no como "poner en
  cero".
- El contrato declaraba `hdu` como nullable (`anyOf: [integer, null]`) pero la API rechazaba el
  literal `null` con un 422: el spec promete algo que ningún cliente podía usar. Schemathesis lo
  detectó al agregar el endpoint nuevo.

---

## User Stories

### Descarga de imágenes

#### US5 - Elegir qué imagen de Hubble bajar

##### Actor/es

- Usuario

##### Funcionalidad

Como usuario, quiero ver los candidatos que ofrece Hubble para un objeto y elegir cuál bajar, en
lugar de que el sistema decida por mí.

##### Valor aportado

Un mismo objeto tiene varias misiones, instrumentos y filtros. La imagen correcta depende de qué
se quiera mirar, así que la elección es del usuario.

##### Criterios de aceptación

- Al buscar un objeto veo el listado de candidatos con instrumento, filtro y tamaño.
- El listado se pagina: no se descargan todas las páginas de Hubble para mostrar la primera.
- Elijo un candidato y la descarga empieza, informada como una transferencia.
- Si el objeto no tiene productos science utilizables, el error se explica.

---

#### US6 - Bajar una imagen grande sin perder el progreso

##### Actor/es

- Usuario

##### Funcionalidad

Como usuario, quiero ver el progreso de una descarga en curso, poder cancelarla y retomarla más
tarde, sin volver a empezar de cero.

##### Valor aportado

Las imágenes de Hubble pesan cientos de MB. Un corte de conexión no debería costar el trabajo
hecho, y la persona tiene que saber si sigue avanzando.

##### Criterios de aceptación

- Veo bytes transferidos y porcentaje mientras la imagen baja.
- Al recargar la página veo el estado de la transferencia y la imagen aparece en el listado al terminar.
- Una transferencia cancelada se puede volver a retomar desde donde estaba.
- Los trozos intermedios no quedan ocupando espacio en el bucket una vez guardada la imagen.

---

### Detección de fuentes

#### US7 - Detectar nebulosa y filamentos, no solo estrellas

##### Actor/es

- Usuario

##### Funcionalidad

Como usuario, quiero detectar fuentes extendidas además de las puntuales, con parámetros propios,
y verlas marcadas sobre la imagen.

##### Valor aportado

La mitad de lo que hay en una imagen de Hubble no son puntos. Un detector que solo encuentra
estrellas deja fuera la nebulosa que uno fue a mirar.

##### Criterios de aceptación

- En la sección Fuentes puedo pedir una detección de fuentes extendidas con sigma, suavizado, área y
  operaciones morfológicas.
- Las regiones extendidas aparecen como marcadores propios, distintas de las puntuales, y se
  comportan bien con el zoom y el pan.
- Los parámetros extendidos son independientes de los puntuales: cambiar unos no pisa los otros.
- Si no hay nada que detectar, el estado se comunica como vacío y no como error.

---

#### US8 - Que los parámetros salgan de la imagen y no de mi intuición

##### Actor/es

- Usuario

##### Funcionalidad

Como usuario, quiero que la aplicación mida el núcleo de las fuentes de esta imagen y me proponga
los parámetros de detección a partir de esa medida.

##### Valor aportado

Los valores por defecto están calibrados para una imagen promedio. En una más borrosa o más
nítida, dan resultados que no se pueden entender ni corregir a ojo.

##### Criterios de aceptación

- En la sección Fuentes hay una acción para pedir la recomendación.
- Al pedirla, los campos de detección quedan con los valores recomendados y veo con qué se
  calculó (FWHM medido, cuántas fuentes se usaron, qué tan dispersas estaban).
- Los parámetros que la medición no toca quedan como yo los tenía.
- Si la imagen no tiene fuentes suficientes para medir, los campos no cambian y se explica por qué.
- Si la única diferencia con mis valores es de redondeo, el preset deja de figurar como propio y
  vuelve al preset con el que coincide.

---

### Verificación con Gaia

#### US9 - Confirmar las detecciones contra un catálogo real

##### Actor/es

- Usuario

##### Funcionalidad

Como usuario, quiero cruzar las fuentes detectadas con Gaia para saber cuáles son estrellas
conocidas y cuáles son ruido o artefactos.

##### Valor aportado

Un círculo en la imagen no es una estrella. El cruce con un catálogo da la probabilidad de que lo
detectado sea un objeto real y con qué parámetros.

##### Criterios de aceptación

- Puedo pedir la verificación de las detecciones actuales para una fuente concreta.
- La consulta al archivo no bloquea la interfaz: puedo seguir usando el visor.
- Veo, por fuente, si hubo coincidencia y con qué probabilidad y distancia.
- Si la consulta falla o Gaia no responde, el estado se comunica y las detecciones no se pierden.

---

### Glosario y ayudas contextuales

#### US10 - Entender los términos que veo en pantalla

##### Actor/es

- Usuario

##### Funcionalidad

Como usuario, quiero consultar el significado de un término del inspector desde el mismo lugar
donde lo veo.

##### Valor aportado

"FWHM", "sigma" o "score" no se explican solos. Tener que buscar documentación externa corta el
uso de la herramienta.

##### Criterios de aceptación

- Los rótulos técnicos del inspector tienen un indicador que abre su definición.
- La definición enlaza a la entrada del glosario.
- El glosario agrupa las entradas por tema (imagen, vista, fuentes, uso del visor) y se puede
  filtrar por texto.

---

## Tareas

### Descarga de imágenes

#### T3 - Descargas reanudables desde Hubble

##### Objetivo

Poder bajar un producto science grande por partes, con progreso, cancelación y reanudación.

##### Resultado esperado

- La búsqueda devuelve candidatos paginados y el usuario elige uno.
- La transferencia expone estado y bytes transferidos, y se puede cancelar y retomar.
- Los trozos se purgan al completar la transferencia.
- Una descarga interrumpida se retoma desde el último trozo guardado.

---

### Detección de fuentes

#### T4 - Detección extendida y preset recomendado

##### Objetivo

Detectar también estructura extendida, y derives los umbrales de detección de la medida del PSF de
la propia imagen.

##### Resultado esperado

- Los parámetros extendidos viajan por el mismo contrato de detección y no pisan los puntuales.
- El endpoint de recomendación devuelve los umbrales medidos, cuáles cambió y con qué evidencia.
- La medición es adaptativa (la ventana crece hasta cubrir 4.5σ) y el resultado se guarda en caché
  por registro, cliente y HDU.
- El frontend ofrece la recomendación como acción explícita y aplica los valores sin pisar lo que
  el usuario escribió.

---

### Verificación con Gaia

#### T5 - Verificación con Gaia DR4

##### Objetivo

Cruzar las detecciones con el catálogo Gaia para confirmar cuáles son estrellas reales.

##### Resultado esperado

- La consulta se resuelve como un job consultable, no bloqueando el request.
- La respuesta dice, por fuente, si hubo coincidencia y con qué probabilidad.
- Los errores del archivo de Gaia se traducen a un estado que la interfaz puede mostrar.

---

### Glosario y ayudas contextuales

#### T6 - Glosario y guías contextuales en el inspector

##### Objetivo

Que ningún parámetro del inspector quede sin explicación dentro de la misma app.

##### Resultado esperado

- Cada control técnico tiene un tooltip con su definición.
- El glosario está paginado por tema y filtrable por texto.
- El contrato de los conceptos del inspector y las entradas del glosario se mantienen en sync.