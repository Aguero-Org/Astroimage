import type { OnboardingTour } from "./types";

export const primerosPasos: OnboardingTour = {
  id: "primeros-pasos",
  route: "/",
  label: "Recorrido por la búsqueda",
  steps: [
    {
      target: '[data-testid="home-title"]',
      title: "Astroimage",
      content:
        "Explorá imágenes del telescopio Hubble y tus propios archivos FITS.",
      placement: "bottom",
    },
    {
      target: '[data-testid="search-input"]',
      title: "Buscá un objeto",
      content:
        "Escribí el nombre de un objeto, un archivo o un instrumento. Probá con NGC 1300.",
      placement: "bottom",
    },
    {
      target: '[data-testid="image-list"]',
      title: "Imágenes disponibles",
      content:
        "Cada ficha es un FITS guardado. La miniatura y el nombre de archivo abren el visor.",
      placement: "top",
      requires: '[data-testid="image-list"]',
    },
    {
      target: '[data-testid="image-list-item-open"]',
      title: "Abrí el visor",
      content:
        "El nombre de archivo lleva al visor, con los controles de render, fuentes y catálogos.",
      placement: "right",
      requires: '[data-testid="image-list-item-open"]',
    },
    {
      target: '[data-testid="edit-image"]',
      title: "Editá la ficha",
      content:
        "Cambiá el título, la descripción y las etiquetas de una imagen guardada.",
      placement: "left",
      requires: '[data-testid="edit-image"]',
    },
    {
      target: '[data-testid="download-stored-fits"]',
      title: "Descargá el FITS",
      content:
        "Baja el archivo original tal como se guardó, sin re-renderizarlo.",
      placement: "left",
      requires: '[data-testid="download-stored-fits"]',
    },
    {
      target: '[data-testid="delete-image"]',
      title: "Eliminá una imagen",
      content: "Borra la imagen del servidor. El original en MAST no se toca.",
      placement: "left",
      requires: '[data-testid="delete-image"]',
    },
    {
      target: '[data-testid="import-fits"]',
      title: "Importá tus FITS",
      content:
        "Subí archivos de tu computadora o un enlace http, https o mast: de dos dimensiones.",
      placement: "bottom",
    },
    {
      target: '[data-testid="home-glossary"]',
      title: "Glosario",
      content:
        "Cada término técnico tiene su explicación, desde el visor hasta los catálogos.",
      placement: "left",
    },
    {
      target: '[data-testid="theme-toggle"]',
      title: "Tema claro u oscuro",
      content:
        "Cambiá el tema cuando quieras. La elección queda guardada en este navegador.",
      placement: "left",
    },
  ],
};
