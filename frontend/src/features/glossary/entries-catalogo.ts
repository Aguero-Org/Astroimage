import type { GlossaryEntry } from "./glossary-types";

export const CATALOGOS_ENTRIES: GlossaryEntry[] = [
  {
    id: "exploracion-cientifica",
    name: "Exploración científica",
    group: "catalogos",
    what: "Panel lateral con catálogos de VizieR y publicaciones sugeridas para la zona del cielo que cubre la imagen.",
    inApp:
      "Se abre cuando termina el análisis de Gaia o cuando llega el cruce con SIMBAD. Reúne catálogos, publicaciones y objetos SIMBAD en tres solapas.",
    where: "Imagen → Exploración científica (lateral derecho)",
  },
  {
    id: "catalogo-vizier",
    name: "Catálogo de VizieR",
    group: "catalogos",
    what: "Conjunto de datos astronómicos publicados (estrellas, galaxias, mediciones) que cubre una región del cielo.",
    inApp:
      "Cada tarjeta muestra un catálogo rankeado para esta imagen, con su título, autores, descripción y enlaces a VizieR y a su ReadMe.",
    where: "Imagen → Exploración científica → Catálogos",
  },
  {
    id: "region-consultada",
    name: "Región consultada",
    group: "catalogos",
    what: "Centro y radio en el cielo que se usan para buscar catálogos que cubran la imagen.",
    inApp:
      "Se calcula a partir de la posición (WCS) de la imagen. La vista previa y las coordenadas se muestran en el encabezado del panel.",
    where: "Imagen → Exploración científica (encabezado)",
  },
  {
    id: "referencia-publicacion",
    name: "Referencia bibliográfica",
    group: "catalogos",
    what: "Identificador de una publicación científica: bibcode (ADS) o DOI.",
    inApp:
      "La tarjeta se titula con el título del artículo cuando ADS lo devuelve, y muestra un extracto del abstract. Al pasar el cursor se abre en ADS o por su DOI.",
    where: "Imagen → Exploración científica → Publicaciones",
  },
  {
    id: "recomendacion-catalogo",
    name: "Motivo de la recomendación",
    group: "catalogos",
    what: "Explicación de por qué el catálogo se propone para esta imagen.",
    inApp:
      "Solo aparece si el objeto buscado está en el catálogo, con el identificador encontrado. La lista ya son catálogos de esta región, así que eso no se repite.",
    where: "Imagen → Exploración científica → Catálogos",
  },
  {
    id: "coincidencia-objeto",
    name: "Coincidencia por objeto",
    group: "catalogos",
    what: "Grado de coincidencia entre el objeto buscado y las filas de un catálogo.",
    inApp:
      "'Objeto identificado' significa que el identificador aparece en el catálogo; 'Solo catálogo' indica cobertura de la región sin coincidencia de objeto.",
    where: "Imagen → Exploración científica → Catálogos",
  },
  {
    id: "publicacion-vizier",
    name: "Publicación asociada",
    group: "catalogos",
    what: "Artículo científico que describe o acompaña a un catálogo, identificado por su Bibcode o DOI.",
    inApp:
      "La solapa Publicaciones los lista como tarjetas. Pasar el cursor abre el artículo en ADS o por su DOI.",
    where: "Imagen → Exploración científica → Publicaciones",
  },
  {
    id: "radio-cruce",
    name: "Radio de cruce",
    group: "catalogos",
    what: "Distancia máxima, en segundos de arco, entre una detección de la imagen y una fuente del catálogo para considerarlas la misma.",
    inApp:
      "Se ajusta en Inspector → Fuentes para Gaia y SIMBAD. Un radio más grande encuentra más contrapartes y también admite más falsos positivos. Selección y las tarjetas de SIMBAD muestran la separación de la mejor contraparte.",
    where: "Inspector → Fuentes y Selección; Exploración científica → SIMBAD",
  },
  {
    id: "exponente-probabilidad",
    name: "Exponente de probabilidad",
    group: "catalogos",
    what: "Potencia que controla cuánto baja la probabilidad a medida que la contraparte se aleja del centro del radio de cruce.",
    inApp:
      "Se ajusta en Inspector → Fuentes. Con un exponente más alto, una separación grande castiga más la probabilidad. Selección y las tarjetas de SIMBAD muestran el valor resultante.",
    where: "Inspector → Fuentes y Selección; Exploración científica → SIMBAD",
  },
];
