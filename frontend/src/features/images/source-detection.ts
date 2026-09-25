import type { DetectSourcesParams } from "@/api/generated/model";
import type { NamedPreset } from "./named-preset";

export type SourceDetectionParams = Omit<DetectSourcesParams, "hdu">;

export const DEFAULT_SOURCE_DETECTION_PARAMS: SourceDetectionParams = {
  fwhm: 3,
  sigma: 5,
  min_snr: 5,
  min_score: 0.18,
  min_distance: 3,
  visual_weight: 0.8,
  visual_area_radius: 7,
  visual_area_sigma: 2,
  max_sources: 50,
};

export const SOURCE_DETECTION_PRESETS: NamedPreset<SourceDetectionParams>[] = [
  {
    id: "equilibrio",
    label: "Equilibrio",
    outcome: "Las estrellas que se ven claro, un número manejable de marcas.",
    hint: "Primera detección.",
    values: DEFAULT_SOURCE_DETECTION_PARAMS,
  },
  {
    id: "mucho-ruido",
    label: "Mucho ruido",
    outcome: "Pocas marcas, las más seguras. Casi no hay falsos en el fondo.",
    hint: "El equilibrio clava granito o basura. En un campo pobre puede quedar vacío.",
    values: {
      fwhm: 3,
      sigma: 10,
      min_snr: 9,
      min_score: 0.35,
      min_distance: 5,
      visual_weight: 0.75,
      visual_area_radius: 7,
      visual_area_sigma: 2.5,
      max_sources: 20,
    },
  },
  {
    id: "baja-resolucion",
    label: "Baja resolución",
    outcome:
      "Una marca por estrella gorda o borrosa, no dos puntos en el mismo disco.",
    hint: "Los perfiles se ven anchos. Si las estrellas son chicas y están apretadas, se come vecinas.",
    values: {
      fwhm: 8,
      sigma: 5,
      min_snr: 5,
      min_score: 0.18,
      min_distance: 8,
      visual_weight: 0.8,
      visual_area_radius: 12,
      visual_area_sigma: 1.5,
      max_sources: 50,
    },
  },
  {
    id: "muchas-estrellas",
    label: "Muchas estrellas",
    outcome: "Más marcas, también débiles y pegadas.",
    hint: "Cúmulo o chip lleno. No en nebulosa: toma nudos de gas por estrellas.",
    values: {
      fwhm: 2.5,
      sigma: 4,
      min_snr: 4,
      min_score: 0.1,
      min_distance: 2,
      visual_weight: 0.8,
      visual_area_radius: 5,
      visual_area_sigma: 1.5,
      max_sources: 150,
    },
  },
];

export const FITS_RENDER_IMAGE_KEY = "fits-render";
