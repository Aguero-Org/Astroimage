import type { OnboardingTour } from "./types";

export const glosario: OnboardingTour = {
  id: "glosario",
  route: "/glossary",
  label: "Recorrido por el glosario",
  steps: [
    {
      target: '[data-testid="glossary-header"]',
      title: "Glosario",
      content:
        "Las palabras que aparecen en el visor, explicadas como se usan en la pantalla.",
      placement: "bottom",
    },
    {
      target: '[data-testid="glossary-search"]',
      title: "Buscá un término",
      content: "Escribí una palabra, como FWHM, y la lista se filtra.",
      placement: "bottom",
    },
    {
      target: '[data-testid="glossary-toc"]',
      title: "En esta página",
      content:
        "Índice de secciones y artículos. El que estás leyendo queda resaltado.",
      placement: "right",
    },
    {
      target: '[data-testid^="glossary-copy-"]',
      title: "Cada término",
      content:
        "Trae la definición, dónde lo ves en la aplicación y un ícono para copiar el enlace directo.",
      placement: "bottom",
      requires: '[data-testid^="glossary-copy-"]',
    },
  ],
};
