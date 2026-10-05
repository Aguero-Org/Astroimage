import type { GlossaryEntry } from "./glossary-types";

export const VISOR_ENTRIES: GlossaryEntry[] = [
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
    what: "Datos de la marca que acabás de elegir, puntual o extendida.",
    inApp:
      "Un clic en un punto muestra SNR, score, pico y flujo. Un clic en un recuadro muestra área, ancho, alto y media. Si hubo cruce con Gaia, también el id.",
    where: "Inspector → Selección",
  },
  {
    id: "copiar-dato",
    name: "Copiar dato",
    group: "visor",
    what: "Copia al portapapeles un valor del inspector, o todos los de un grupo.",
    inApp:
      "Al pasar el cursor, el dato o el título del grupo se subraya y aparece el ícono de copia. El título copia todas las líneas del grupo. Un aviso confirma que se copió.",
    where: "Inspector",
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
