import type { GlossaryEntry } from "./glossary-types";

export const VISTA_ENTRIES: GlossaryEntry[] = [
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
    inApp: "Mayor que 1 aclara medios tonos; menor que 1 los oscurece.",
    where: "Inspector → Vista",
  },
  {
    id: "preset-vista",
    name: "Preset de vista",
    group: "vista",
    what: "Conjunto de stretch, límites y color con un nombre de situación (equilibrio, mucho ruido, mucho brillo…).",
    inApp: "Rellena el formulario. Si editás un campo, pasa a Personalizado.",
    where: "Inspector → Vista",
  },
];
