import {
  focusScientificTab,
  openInspector,
  selectFirstSource,
} from "../tour-actions";
import { GAIA_MARKER, NO_GAIA_MARKER, SIMBAD_MARKER } from "./selectors";
import type { OnboardingTour } from "./types";

export const visor: OnboardingTour = {
  id: "visor",
  route: "/image",
  label: "Recorrido por el visor",
  steps: [
    {
      target: '[data-testid="image-detail-title"]',
      title: "Ficha de la imagen",
      content:
        "El nombre del objeto y su catálogo, siempre a la vista sobre el visor.",
      placement: "bottom",
    },
    {
      target: '[data-testid="fits-viewer"]',
      title: "Visor FITS",
      content:
        "Arrastrá para mover y usá la rueda o el doble clic para acercar. Los recuadros marcan las fuentes detectadas.",
      placement: "center",
    },
    {
      target: '[data-testid="fits-toolbar-zoom-in"]',
      title: "Controles de la vista",
      content: "Acercá, alejá, ajustá el encuadre o pasá a pantalla completa.",
      placement: "left",
    },
    {
      target: GAIA_MARKER,
      title: "Punto verde: match Gaia",
      content:
        "La detección coincide con una estrella del catálogo Gaia en posición. Es un cruce confirmado.",
      placement: "right",
      requires: GAIA_MARKER,
    },
    {
      target: NO_GAIA_MARKER,
      title: "Punto violeta: sin match Gaia",
      content:
        "Se detectó sobre la imagen, pero Gaia no tiene un candidato factible en esa posición.",
      placement: "right",
      requires: NO_GAIA_MARKER,
    },
    {
      target: SIMBAD_MARKER,
      title: "Marca con insignia SIMBAD",
      content:
        "El círculo se cruza con un objeto SIMBAD. La insignia lo marca y el objeto aparece en el panel SIMBAD.",
      placement: "right",
      requires: SIMBAD_MARKER,
    },
    {
      target: '[data-testid="inspector-toggle"]',
      title: "Inspector",
      content:
        "Abre el panel de la izquierda con el render, la detección de fuentes y los metadatos.",
      placement: "right",
    },
    {
      target: '[data-testid="inspector-section-view-toggle"]',
      title: "Vista",
      content:
        "El histograma y los controles de render: estiramiento, límites y mapa de color.",
      placement: "right",
      before: openInspector,
    },
    {
      target: '[data-testid="inspector-section-sources-toggle"]',
      title: "Fuentes",
      content:
        "Lanzá el análisis y mirá el resumen de puntuales y extendidas. Debajo están los cruces.",
      placement: "right",
    },
    {
      target: '[data-testid="gaia-cross-match"]',
      title: "Cruce con Gaia",
      content:
        "Cuántas de las fuentes detectadas coincidieron con Gaia. En la imagen se ven verdes.",
      placement: "right",
      requires: '[data-testid="gaia-cross-match"]',
    },
    {
      target: '[data-testid="inspector-section-selection-toggle"]',
      title: "Selección",
      content:
        "Elegí una marca y acá ves sus datos: SNR, coordenadas y el match Gaia si lo tiene.",
      placement: "right",
      before: selectFirstSource,
    },
    {
      target: '[data-testid="scientific-toggle"]',
      title: "Exploración científica",
      content:
        "Abre el panel de la derecha con catálogos, publicaciones y objetos SIMBAD de la región.",
      placement: "left",
    },
    {
      target: '[data-testid="scientific-tab-catalogs"]',
      title: "Catálogos",
      content:
        "Recomendaciones de catálogos para la posición y el campo de la imagen.",
      placement: "left",
      before: () => focusScientificTab("scientific-tab-catalogs"),
    },
    {
      target: '[data-testid="scientific-tab-papers"]',
      title: "Publicaciones",
      content:
        "Papers que citan o usan esa región del cielo, con su identificador.",
      placement: "left",
      before: () => focusScientificTab("scientific-tab-papers"),
    },
    {
      target: '[data-testid="scientific-tab-simbad"]',
      title: "SIMBAD",
      content:
        "Objetos SIMBAD cercanos a las fuentes. Los que hacen match quedan marcados en la imagen y con insignia.",
      placement: "left",
      before: () => focusScientificTab("scientific-tab-simbad"),
    },
  ],
};
