import type { DetectSourcesParams } from "@/api/generated/model";
import type { NamedPreset } from "./named-preset";

export type SourceDetectionParams = Omit<DetectSourcesParams, "hdu">;

export const DEFAULT_SOURCE_DETECTION_PARAMS: SourceDetectionParams = {
  fwhm: 5.5,
  sigma: 9,
  min_snr: 6,
  min_score: 0.18,
  min_distance: 4,
  visual_weight: 0.8,
  visual_area_radius: 7,
  visual_area_sigma: 2,
  max_sources: 50,
};

export const SOURCE_DETECTION_PRESETS: NamedPreset<SourceDetectionParams>[] = [
  {
    id: "estandar",
    label: "Estándar",
    outcome:
      "Las estrellas que se ven claro, un número manejable de marcas, las más visibles arriba.",
    hint: "Usala como primera detección.",
    values: DEFAULT_SOURCE_DETECTION_PARAMS,
  },
  {
    id: "conservador",
    label: "Conservador",
    outcome: "Pocas marcas, las más seguras. Casi no hay falsos.",
    hint: "Usala para revisar a mano o cuando el estándar marca basura. En un campo pobre o de estrellas débiles puede quedar casi vacío.",
    values: {
      fwhm: 5.5,
      sigma: 12,
      min_snr: 10,
      min_score: 0.35,
      min_distance: 5,
      visual_weight: 0.75,
      visual_area_radius: 7,
      visual_area_sigma: 2.5,
      max_sources: 20,
    },
  },
  {
    id: "campo-denso",
    label: "Campo denso",
    outcome: "Muchas más marcas, también débiles y pegadas.",
    hint: "Usala en cúmulos o chips llenos de estrellas. No en nebulosa: va a clavar nudos de gas como si fueran estrellas. Tampoco si la imagen está borrosa.",
    values: {
      fwhm: 4,
      sigma: 5,
      min_snr: 4,
      min_score: 0.1,
      min_distance: 3,
      visual_weight: 0.8,
      visual_area_radius: 5,
      visual_area_sigma: 1.5,
      max_sources: 150,
    },
  },
  {
    id: "seeing-ancho",
    label: "Seeing ancho",
    outcome:
      "Marcas más separadas, pensadas para estrellas gordas o una imagen poco nítida.",
    hint: "Usala si ves discos grandes y el estándar pone dos puntos en la misma estrella. Si las estrellas son chicas y están apretadas, se come vecinas.",
    values: {
      fwhm: 9,
      sigma: 8,
      min_snr: 6,
      min_score: 0.18,
      min_distance: 8,
      visual_weight: 0.8,
      visual_area_radius: 12,
      visual_area_sigma: 1.5,
      max_sources: 50,
    },
  },
  {
    id: "lo-mas-brillante",
    label: "Lo más brillante",
    outcome:
      "Las mismas detecciones que el estándar, ordenadas por intensidad, no por quién se ve más grande.",
    hint: "Usala si arriba del ranking hay manchas y abajo estrellas nítidas. No suma fuentes nuevas.",
    values: {
      ...DEFAULT_SOURCE_DETECTION_PARAMS,
      visual_weight: 0.25,
      min_score: 0.15,
    },
  },
];

export const FITS_RENDER_IMAGE_KEY = "fits-render";
