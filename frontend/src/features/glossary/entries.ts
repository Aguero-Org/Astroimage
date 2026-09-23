export const GLOSSARY_GROUPS = [
  { id: "imagen", title: "Imagen y archivo" },
  { id: "vista", title: "Cómo se ve la imagen" },
  { id: "fuentes", title: "Fuentes" },
  { id: "visor", title: "Uso del visor" },
] as const;

export type GlossaryGroupId = (typeof GLOSSARY_GROUPS)[number]["id"];

export type GlossaryEntry = {
  id: string;
  name: string;
  group: GlossaryGroupId;
  what: string;
  inApp: string;
  where: string;
};

export const GLOSSARY_ENTRIES: GlossaryEntry[] = [
  {
    id: "fits",
    name: "FITS",
    group: "imagen",
    what: "Formato de archivo de astronomía: imagen más encabezado con datos de la observación.",
    inApp: "Astroimage abre un FITS, lo muestra como PNG y lee sus metadatos.",
    where: "Inicio (listado) y visor",
  },
  {
    id: "objeto",
    name: "Objeto celeste",
    group: "imagen",
    what: "Nombre con el que buscás el cielo: M31, NGC 1300, Orión…",
    inApp: "La búsqueda pide ese nombre al archivo Hubble y lista recortes.",
    where: "Inicio",
  },
  {
    id: "hdu",
    name: "HDU",
    group: "imagen",
    what: "Capa o extensión dentro de un FITS. Un archivo puede traer varias imágenes.",
    inApp:
      "Render, histograma y detección usan el mismo HDU. Si hay uno solo, no se muestra el selector.",
    where: "Inspector (encabezado)",
  },
  {
    id: "metadatos",
    name: "Metadatos del archivo",
    group: "imagen",
    what: "Datos del instrumento, tamaño, coordenadas en el cielo y encabezado FITS.",
    inApp: "Se agrupan en Archivo. El encabezado crudo queda cerrado.",
    where: "Inspector → Archivo",
  },
  {
    id: "wcs",
    name: "WCS",
    group: "imagen",
    what: "Solución que traduce píxeles a coordenadas en el cielo (RA, Dec) cuando existe.",
    inApp:
      "Archivo indica si hay WCS. Sin WCS las fuentes se marcan solo en píxeles.",
    where: "Inspector → Archivo",
  },
  {
    id: "instrumento",
    name: "Instrumento",
    group: "imagen",
    what: "Telescopio, cámara, filtro y tiempo de exposición de la toma.",
    inApp:
      "El grupo Instrumento en Archivo. No siempre vienen todos los campos.",
    where: "Inspector → Archivo",
  },
  {
    id: "imagen-pixeles",
    name: "Datos de la imagen",
    group: "imagen",
    what: "Tamaño, unidad y estadísticas de los píxeles (mínimo, máximo, mediana, fondo).",
    inApp: "El grupo Imagen en Archivo describe el HDU que estás viendo.",
    where: "Inspector → Archivo",
  },
  {
    id: "fotometria",
    name: "Fotometría",
    group: "imagen",
    what: "Constantes del filtro (PHOTFLAM, longitud de onda, ancho de banda) para pasar de cuentas a flujo.",
    inApp: "El grupo Fotometría aparece solo si el FITS trae esas claves.",
    where: "Inspector → Archivo",
  },
  {
    id: "encabezado",
    name: "Header FITS",
    group: "imagen",
    what: "Lista cruda de palabras clave del encabezado (DATE-OBS, TELESCOP…).",
    inApp:
      "Queda cerrada al final de Archivo. El resto de grupos ya interpreta lo útil.",
    where: "Inspector → Archivo",
  },
  {
    id: "tabla-fits",
    name: "Tabla FITS",
    group: "imagen",
    what: "Tabla binaria embebida (catálogo o calibración), no es un plano de imagen.",
    inApp:
      "Si el archivo trae tablas, se listan en Archivo. No se pintan en el visor.",
    where: "Inspector → Archivo",
  },
  {
    id: "stretch",
    name: "Stretch",
    group: "vista",
    what: "Cómo se comprime el brillo para que se vea en pantalla (lineal, raíz, log, asinh).",
    inApp:
      "Cambia el PNG: log y asinh resaltan estructura débil; lineal muestra picos crudos.",
    where: "Inspector → Vista",
  },
  {
    id: "limits",
    name: "Límites",
    group: "vista",
    what: "Cómo se elige el rango de intensidad que se pinta: percentiles o ZScale.",
    inApp:
      "Percentiles recorta colas; ZScale ayuda si la imagen se ve negra o quemada.",
    where: "Inspector → Vista",
  },
  {
    id: "colormap",
    name: "Mapa de color",
    group: "vista",
    what: "Paleta con la que se colorea el PNG. No inventa nebulosa; solo pinta niveles.",
    inApp: "Gris es el default. Otras paletas sirven para distinguir niveles.",
    where: "Inspector → Vista",
  },
  {
    id: "histogram",
    name: "Histograma",
    group: "vista",
    what: "Distribución de valores de píxel del HDU actual.",
    inApp: "Las líneas marcan Pmin y Pmax cuando usás percentiles.",
    where: "Inspector → Vista",
  },
  {
    id: "pmin",
    name: "Pmin",
    group: "vista",
    what: "Percentil inferior del recorte (0–100).",
    inApp: "Subirlo oculta fondo. Debe ser menor que Pmax.",
    where: "Inspector → Vista",
  },
  {
    id: "pmax",
    name: "Pmax",
    group: "vista",
    what: "Percentil superior del recorte (0–100).",
    inApp: "Bajarlo satura menos las estrellas brillantes.",
    where: "Inspector → Vista",
  },
  {
    id: "gamma",
    name: "Gamma",
    group: "vista",
    what: "Curva extra de brillo sobre el stretch.",
    inApp: "Menor que 1 aclara medios tonos; mayor que 1 los oscurece.",
    where: "Inspector → Vista",
  },
  {
    id: "preset-vista",
    name: "Preset de vista",
    group: "vista",
    what: "Conjunto de stretch, límites y color con un nombre (estándar, cielo profundo…).",
    inApp: "Rellena el formulario. Si editás un campo, pasa a Personalizado.",
    where: "Inspector → Vista",
  },
  {
    id: "fuente-puntual",
    name: "Fuente puntual",
    group: "fuentes",
    what: "Objeto compacto (estrella, quasar) que en la imagen es un pico, no una mancha extendida.",
    inApp: "Se marca con un punto. Al hacer clic, sus números van a Selección.",
    where: "Visor y Inspector → Selección",
  },
  {
    id: "deteccion",
    name: "Detección de fuentes",
    group: "fuentes",
    what: "Búsqueda automática de picos sobre el fondo de la imagen.",
    inApp: "Corre con los parámetros de Fuentes y dibuja marcas sobre el FITS.",
    where: "Inspector → Fuentes",
  },
  {
    id: "fwhm",
    name: "FWHM",
    group: "fuentes",
    what: "Ancho a media altura del núcleo estelar, en píxeles.",
    inApp:
      "Valores más altos buscan estrellas más gordas o una imagen poco nítida.",
    where: "Inspector → Fuentes",
  },
  {
    id: "sigma",
    name: "Sigma",
    group: "fuentes",
    what: "Umbral de detección en RMS del fondo.",
    inApp:
      "Más alto exige picos más contrastados y suele devolver menos marcas.",
    where: "Inspector → Fuentes",
  },
  {
    id: "snr",
    name: "SNR",
    group: "fuentes",
    what: "Relación señal / ruido del pico.",
    inApp:
      "El SNR mínimo descarta picos débiles. En Selección ves el SNR de la marca.",
    where: "Inspector → Fuentes y Selección",
  },
  {
    id: "score",
    name: "Score",
    group: "fuentes",
    what: "Puntuación de relevancia (0 a 1) que mezcla aspecto visual y forma.",
    inApp: "Filtra candidatos poco convincentes y ordena el ranking.",
    where: "Inspector → Fuentes y Selección",
  },
  {
    id: "min-distance",
    name: "Distancia mínima",
    group: "fuentes",
    what: "Separación mínima entre picos, en píxeles.",
    inApp: "Evita marcar dos veces la misma estrella.",
    where: "Inspector → Fuentes",
  },
  {
    id: "max-sources",
    name: "Máximo de fuentes",
    group: "fuentes",
    what: "Tope de fuentes a devolver, ordenadas por relevancia.",
    inApp: "0 significa sin límite. Baja el número si hay demasiadas marcas.",
    where: "Inspector → Fuentes",
  },
  {
    id: "visual-weight",
    name: "Peso visual",
    group: "fuentes",
    what: "Cuánto pesa el aspecto visual frente a la morfología en el score.",
    inApp: "0 = solo forma; 1 = solo cómo se ve el parche.",
    where: "Inspector → Fuentes",
  },
  {
    id: "preset-deteccion",
    name: "Preset de detección",
    group: "fuentes",
    what: "Conjunto de umbrales con un nombre (estándar, conservador, campo denso…).",
    inApp: "Rellena Fuentes. Si tocás un número, pasa a Personalizado.",
    where: "Inspector → Fuentes",
  },
  {
    id: "visual-area-radius",
    name: "Radio visual",
    group: "fuentes",
    what: "Radio en píxeles del parche alrededor del pico para medir área, flujo y pico aparentes.",
    inApp: "Más radio mira un entorno más grande; demasiado agarra vecinos.",
    where: "Inspector → Fuentes",
  },
  {
    id: "visual-area-sigma",
    name: "Sigma visual",
    group: "fuentes",
    what: "Umbral local del parche visual, en RMS del fondo.",
    inApp: "Define qué píxeles cuentan como parte de la fuente en ese parche.",
    where: "Inspector → Fuentes",
  },
  {
    id: "rank",
    name: "Rank",
    group: "fuentes",
    what: "Orden de relevancia entre las fuentes detectadas. 1 es la más relevante.",
    inApp: "Aparece en Selección al hacer clic en una marca.",
    where: "Inspector → Selección",
  },
  {
    id: "centroide",
    name: "Centroide",
    group: "fuentes",
    what: "Posición del pico en píxeles (X, Y) sobre el HDU.",
    inApp:
      "X e Y en Selección. No son RA/Dec salvo que haya WCS (aún no se muestran ahí).",
    where: "Inspector → Selección",
  },
  {
    id: "peak",
    name: "Peak",
    group: "fuentes",
    what: "Valor de píxel en el máximo del pico.",
    inApp: "En Selección, si el detector lo calculó.",
    where: "Inspector → Selección",
  },
  {
    id: "flux",
    name: "Flux",
    group: "fuentes",
    what: "Flujo estimado de la fuente puntual (cuentas o unidad del HDU).",
    inApp: "En Selección, si el detector lo calculó.",
    where: "Inspector → Selección",
  },
  {
    id: "mean",
    name: "Media",
    group: "fuentes",
    what: "Valor medio de píxel dentro de la región detectada.",
    inApp: "En Selección, si el detector lo calculó.",
    where: "Inspector → Selección",
  },
  {
    id: "fuente-extendida",
    name: "Fuente extendida",
    group: "fuentes",
    what: "Región no puntual de la imagen: luz difusa con forma, como una nebulosa o una galaxia.",
    inApp:
      "Se marca con un recuadro sobre la imagen y cuenta como 'extendida' en el resumen.",
    where: "Visor (recuadro) e Inspector → Selección",
  },
  {
    id: "area",
    name: "Área",
    group: "fuentes",
    what: "Cantidad de píxeles que ocupa la región extendida detectada.",
    inApp: "Aparece en Selección al marcar una fuente extendida.",
    where: "Inspector → Selección",
  },
  {
    id: "ancho-alto",
    name: "Ancho y alto",
    group: "fuentes",
    what: "Extensión horizontal y vertical, en píxeles, del recuadro que envuelve la región.",
    inApp: "Se muestran en Selección al marcar una fuente extendida.",
    where: "Inspector → Selección",
  },
  {
    id: "ext-sigma",
    name: "Sigma (extendidas)",
    group: "fuentes",
    what: "Umbral en RMS del fondo para abrir regiones de luz difusa.",
    inApp:
      "Más alto exige nebulosas más contrastadas. Lo edita el grupo Fuentes extendidas.",
    where: "Inspector → Fuentes",
  },
  {
    id: "ext-smooth-sigma",
    name: "Suavizado",
    group: "fuentes",
    what: "Suavizado gaussiano previo al umbral para dominar el ruido.",
    inApp:
      "Muy bajo deja ruido que abre regiones falsas; muy alto funde estructuras finas.",
    where: "Inspector → Fuentes",
  },
  {
    id: "ext-binning",
    name: "Factor de bin",
    group: "fuentes",
    what: "Agrupado de píxeles que usa el detector de regiones para acelerar el cálculo.",
    inApp:
      "No cambia el resultado: el área y el umbral se escalan para compensarlo.",
    where: "Inspector → Fuentes",
  },
  {
    id: "ext-min-area",
    name: "Área mínima",
    group: "fuentes",
    what: "Área mínima, en píxeles, para que una región cuente como fuente extendida.",
    inApp: "Regiones más chicas se descartan antes de calcular su relevancia.",
    where: "Inspector → Fuentes",
  },
  {
    id: "ext-max-area",
    name: "Área máxima",
    group: "fuentes",
    what: "Área máxima, en píxeles, de una región extendida.",
    inApp:
      "0 significa sin límite. Útil para separar la nebulosa de un fondo de estructura grande.",
    where: "Inspector → Fuentes",
  },
  {
    id: "ext-closing",
    name: "Cierre",
    group: "fuentes",
    what: "Operación morfológica que rellena huecos y une bordes rotos de una región.",
    inApp:
      "Subirlo ayuda cuando la nebulosa sale cortada en pedazos. 0 desactiva.",
    where: "Inspector → Fuentes",
  },
  {
    id: "ext-opening",
    name: "Apertura",
    group: "fuentes",
    what: "Operación morfológica que corta protuberancias finas y rastro de ruido.",
    inApp:
      "Subirlo limpia la silueta pero puede dividir regiones grandes. 0 desactiva.",
    where: "Inspector → Fuentes",
  },
  {
    id: "inspector",
    name: "Inspector",
    group: "visor",
    what: "Panel lateral con controles y metadatos. La imagen queda al lado.",
    inApp:
      "Se abre con el botón hamburguesa. Cada sección se despliega aparte.",
    where: "Visor",
  },
  {
    id: "seleccion",
    name: "Selección",
    group: "visor",
    what: "Datos de la fuente puntual que acabás de marcar.",
    inApp: "Un clic en un punto llena esta sección (SNR, score, pico, flujo).",
    where: "Inspector → Selección",
  },
  {
    id: "pan-zoom",
    name: "Pan y zoom",
    group: "visor",
    what: "Mover y acercar la imagen en el visor.",
    inApp:
      "Arrastrá para pan. La barra acerca, aleja, ajusta a la vista o pantalla completa.",
    where: "Visor",
  },
];

export function filterGlossaryEntries(
  entries: readonly GlossaryEntry[],
  query: string,
): GlossaryEntry[] {
  const needle = query.trim().toLowerCase();
  if (needle.length === 0) {
    return [...entries];
  }
  return entries.filter((entry) => {
    const haystack = `${entry.name} ${entry.what} ${entry.inApp} ${entry.where}`;
    return haystack.toLowerCase().includes(needle);
  });
}

export function glossaryPath(id: string): string {
  return `/glossary#${id}`;
}
