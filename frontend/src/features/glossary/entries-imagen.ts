import type { GlossaryEntry } from "./glossary-types";

export const IMAGEN_ENTRIES: GlossaryEntry[] = [
  {
    id: "fits",
    name: "FITS",
    group: "imagen",
    what: "Formato de archivo de astronomía: imagen más encabezado con datos de la observación.",
    inApp: "Astroimage abre un FITS, lo muestra como PNG y lee sus metadatos.",
    where: "Inicio (listado) y visor",
  },
  {
    id: "importar-fits",
    name: "Importar FITS",
    group: "imagen",
    what: "Carga de un archivo FITS propio, desde la computadora o desde un enlace http, https o mast:.",
    inApp:
      "El inicio guarda el archivo en el servidor si es una imagen 2D. Arrastrar un archivo sobre la página abre la importación. Un archivo o enlace repetido no se vuelve a guardar.",
    where: "Inicio (listado)",
  },
  {
    id: "etiquetas-imagen",
    name: "Etiquetas",
    group: "imagen",
    what: "Palabras que agregás a una imagen ya guardada para reconocerla.",
    inApp:
      "Se editan desde la ficha del inicio. No modifican el archivo FITS ni el objeto guardado.",
    where: "Inicio (listado)",
  },
  {
    id: "slug-archivo",
    name: "Nombre de archivo",
    group: "imagen",
    what: "Nombre con el que se guardó el FITS al descargarlo.",
    inApp: "La ficha del inicio muestra ese nombre. El enlace abre el visor.",
    where: "Inicio (listado)",
  },
  {
    id: "objeto",
    name: "Objeto celeste",
    group: "imagen",
    what: "Nombre con el que buscás el cielo: M31, NGC 1300, Orión…",
    inApp:
      "El buscador del inicio lo manda al archivo Hubble y lista los recortes, además de aceptar archivo o instrumento.",
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
];
