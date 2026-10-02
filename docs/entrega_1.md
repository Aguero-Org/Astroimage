# Entrega 1 - Astroimage

Documento de la primera entrega posterior a la PoC. La PoC ([[POC-documentacion]]) validó el
núcleo mínimo: buscar un objeto, bajarlo, verlo y detectarle fuentes puntuales. Esta entrega
deja de adivinar: el usuario elige qué imagen bajar, la descarga se puede retomar, y los
parámetros de detección salen de medir la imagen en lugar de ajustarlos a ciegas.

La numeración de User Stories continúa la de la PoC (`US1`–`US4`).

Cada historia cubre **un** requerimiento: las cards que tocaban el mismo requerimiento quedaron
fusionadas en una sola historia en lugar de partirse en varias. Quedan cuatro áreas, una por
historia: **descarga de imágenes**, **detección de fuentes**, **verificación con Gaia** y
**glosario y ayudas contextuales**.

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

# User Stories

## US5 - Bajarse una imagen de Hubble

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero buscar un objeto celeste en Hubble, ver los candidatos que ofrece con
paginación, elegir uno y seguir su descarga aunque se corte, cancelarla y retomarla sin perder lo
ya bajado.

### Valor aportado

Un mismo objeto tiene varias misiones, instrumentos y filtros, así que la imagen correcta depende
de qué se quiera mirar: la elección es del usuario, no del sistema. Y como las imágenes pesan
cientos de MB, un corte de conexión no debería costar el trabajo hecho.

### Reglas de negocio

- La búsqueda exige un nombre de objeto no vacío. Si viene vacío, la API lo rechaza con un 422 sin
  llegar a preguntarle nada a Hubble.
- El listado se pagina de verdad: la página arranca en 1 y el tamaño va de 1 a 50 candidatos, con
  10 por página por defecto. El backend no recorre todas las páginas de Hubble para mostrar la
  primera.
- El servidor dice si hay página siguiente, en vez de dejar que el cliente lo adivine.
- Se puede ordenar por nombre de producto, instrumento, propuesta, filtros, tamaño o fecha de
  observación, en ascendente o descendente.
- Se puede descartar por tamaño mínimo, para no perder tiempo bajando productos que no sirven.
- Cada candidato trae un token opaco. La interfaz no manda la URL de Hubble: manda el token y un
  nombre visible de 1 a 256 caracteres.
- Elegir un candidato es un pedido aparte de la búsqueda, y devuelve una transferencia, no una
  imagen.
- La transferencia expone bytes transferidos, velocidad y progreso. El total y el porcentaje pueden
  venir vacíos mientras el servidor de Hubble todavía no dice cuánto pesa el archivo.
- Al completarse, la transferencia trae el identificador y el slug que ya sirven para abrir la
  imagen.
- La transferencia declara si se puede reanudar.
- La descarga se parte en trozos que se purgan al completarse, para no duplicar el espacio usado.

### Criterios de aceptación

- Al buscar un objeto veo el listado de candidatos con instrumento, filtros, propuesta y tamaño.
- Puedo pasar de página y cambiar el orden sin que la búsqueda vuelva a empezar desde cero.
- Elijo un candidato, le pongo un nombre y la descarga empieza, informada como una transferencia.
- Veo bytes transferidos, velocidad y porcentaje mientras la imagen baja.
- Una descarga cancelada o interrumpida se retoma desde el último trozo guardado, incluso si
  recargué la página.
- Al terminar, la imagen aparece en el listado y puedo abrirla directamente.
- Los trozos intermedios ya no ocupan espacio en el bucket una vez guardada la imagen.
- Si el objeto no tiene productos science utilizables, el error se explica y no queda una
  transferencia colgada.

### Fuera de alcance

- Bajar dos o más candidatos en paralelo: el contrato acepta un token por pedido.
- Fuentes distintas de Hubble.
- Reanudar una transferencia cuyo producto haya cambiado en Hubble desde que empezó.

---

## US6 - Detectar fuentes en la imagen

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero detectar fuentes extendidas además de las puntuales, con sus propios
parámetros, y que la aplicación mida esta imagen y me recomiende los valores de detección.

### Valor aportado

La mitad de lo que hay en una imagen de Hubble no son puntos: un detector que solo encuentra
estrellas deja fuera la nebulosa que uno fue a mirar. Y los parámetros por defecto están calibrados
para una imagen promedio, así que en una más borrosa o más nítida dan resultados que no se pueden
entender ni corregir a ojo.

### Reglas de negocio

- Todos los parámetros de detección son opcionales. Lo que no se manda no se toca: la detección usa
  el valor que ya tenía la vista.
- Las puntuales y las extendidas viajan en el mismo pedido pero en juegos de parámetros separados, y
  modificar unos no pisa los otros.
- Las extendidas tienen su propio sigma, suavizado, área mínima y máxima, factor de binned,
  iteraciones de cierre y apertura, score mínimo y tope de fuentes.
- La respuesta separa las dos familias de marcadores y trae un resumen con cuántas hay de cada tipo.
- El HDU es opcional en todos los pedidos: si no se indica, se usa la primera imagen 2D del
  archivo.
- La recomendación devuelve los valores recomendados, los valores de base, la evidencia y la
  lista de cambios.
- Cada cambio dice qué parámetro se movió, de cuánto a cuánto y por qué. La recomendación es
  auditable, no una caja negra.
- La evidencia dice el FWHM medido, cuántas fuentes se usaron, qué tan dispersas estaban, el RMS
  del fondo, los conteos de cada tipo de fuente y la mediana de SNR.
- Solo se recalculan los umbrales que dependen del PSF. Los que dependen del gusto o del
  instrumento se devuelven intactos.
- Si no hay fuentes suficientes para medir, la evidencia viene vacía, los campos no cambian y la
  interfaz lo explica.
- El resultado de la medición se guarda en caché por registro, cliente y HDU, y la evidencia dice
  si salió de caché.
- Si lo único que cambia es el redondeo, el preset deja de figurar como propio y vuelve al preset
  con el que coincide.
- No detectar nada es un resultado vacío, no un error.

### Criterios de aceptación

- En la sección Fuentes puedo pedir una detección de fuentes extendidas con sigma, suavizado,
  área y operaciones morfológicas.
- Las regiones extendidas aparecen como marcadores propios, distintas de las puntuales, y se
  comportan bien con el zoom y el pan.
- Los parámetros extendidos son independientes de los puntuales: cambiar unos no pisa los otros.
- Hay una acción para pedir la recomendación de parámetros.
- Al pedirla, los campos quedan con los valores recomendados y veo con qué se calculó y qué
  cambió.
- Los parámetros que la medición no toca quedan como yo los tenía.
- Si la imagen no tiene fuentes suficientes para medir, los campos no cambian y se explica por qué.
- Si la única diferencia con mis valores es de redondeo, el preset vuelve al preset con el que
  coincide.
- Si no hay nada que detectar, el estado se comunica como vacío y no como error.

### Fuera de alcance

- Calibración astrométrica o resolución de placas: el preset mide el núcleo, no las coordenadas.
- Comparar detecciones entre imágenes o entre fechas.

---

## US7 - Confirmar las detecciones contra un catálogo real

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero cruzar las fuentes detectadas con Gaia para saber cuáles son estrellas
conocidas y cuáles son ruido o artefactos.

### Valor aportado

Un círculo en la imagen no es una estrella. El cruce con un catálogo da la probabilidad de que lo
detectado sea un objeto real y con qué parámetros.

### Reglas de negocio

- La verificación acepta los mismos parámetros de detección, más el radio de coincidencia y el
  exponente de probabilidad, que controlan cuán exigente es el cruce.
- No es un pedido bloqueante: la API responde que la verificación está pendiente y devuelve un
  identificador de trabajo. El resultado se consulta aparte.
- Mientras tanto se puede seguir usando el visor.
- Por fuente, la respuesta dice si hubo coincidencia, con qué separación, con qué probabilidad, y el
  identificador, las coordenadas y la magnitud G de la estrella de Gaia.
- Por tipo de fuente hay un resumen con cuántas hubo, cuántas coincidieron, el porcentaje y la
  separación mediana.
- La detección incluye un enlace al catálogo para ir de un salto a la fuente original.
- Si el archivo de Gaia no responde, el error se traduce a un estado que la interfaz puede mostrar y
  las detecciones no se pierden.

### Criterios de aceptación

- Puedo pedir la verificación de las detecciones actuales para una fuente concreta.
- La consulta no bloquea la interfaz: puedo seguir usando el visor.
- Veo, por fuente, si hubo coincidencia y con qué probabilidad y separación.
- Veo el resumen por tipo de fuente, con el porcentaje de coincidencia.
- Puedo saltar al catálogo desde la fuente verificada.
- Si la consulta falla o Gaia no responde, el estado se comunica y las detecciones no se pierden.

### Fuera de alcance

- Consultas a catálogos distintos de Gaia DR4.
- Correr la verificación automáticamente en cada detección.

---

## US8 - Consultar el glosario desde el inspector

### Actor/es

- Usuario

### Funcionalidad

Como usuario, quiero consultar el significado de un término del inspector desde el mismo lugar
donde lo veo, sin salir de la aplicación.

### Valor aportado

"FWHM", "sigma" o "score" no se explican solos. Tener que buscar documentación externa corta el
uso de la herramienta, y encima obliga a reconstruir después qué parámetro era el que no se
entendía.

### Reglas de negocio

- El glosario tiene 52 entradas repartidas en cuatro temas: imagen y archivo, cómo se ve la
  imagen, fuentes y uso del visor.
- Cada entrada dice qué es el término, cómo aparece en la aplicación y dónde se lo encuentra. No
  alcanza con una definición de diccionario.
- Los rótulos técnicos del inspector llevan un indicador que abre la definición en el lugar.
- Desde la definición se llega a la entrada completa del glosario.
- La página del glosario agrupa por tema y filtra por texto.
- El filtro busca tanto por el nombre de la entrada como por el texto de la definición.
- Las entradas y los tooltips comparten el mismo tipo de dato, así que un término no puede quedar
  con una definición en un lado y otra en el otro.

### Criterios de aceptación

- Los rótulos técnicos del inspector tienen un indicador que abre su definición.
- La definición enlaza a la entrada del glosario.
- El glosario agrupa las entradas por tema y se puede filtrar por texto.
- El filtro encuentra una entrada tanto por su nombre como por una palabra de su definición.
- Buscar un término que aparece en varias entradas me devuelve todas.

### Fuera de alcance

- Glosarios editables por el usuario.
- Traducción a otros idiomas.

