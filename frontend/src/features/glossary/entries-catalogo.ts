import type { GlossaryEntry } from "./glossary-types";

export const CATALOGOS_ENTRIES: GlossaryEntry[] = [
  {
    id: "exploracion-cientifica",
    name: "Exploración científica",
    group: "catalogos",
    what: "Panel lateral con catálogos de VizieR y publicaciones sugeridas para la zona del cielo que cubre la imagen.",
    inApp:
      "Se abre solo cuando termina el análisis de Gaia. Reúne catálogos y publicaciones en dos solapas.",
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
];
