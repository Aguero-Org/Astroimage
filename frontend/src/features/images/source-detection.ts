import type { DetectSourcesParams } from "@/api/generated/model";
import type { NamedPreset } from "./named-preset";

export const POINT_DETECTION_KEYS = [
  "fwhm",
  "sigma",
  "min_snr",
  "min_score",
  "min_distance",
  "visual_weight",
  "visual_area_radius",
  "visual_area_sigma",
  "max_sources",
] as const;

export const EXTENDED_DETECTION_KEYS = [
  "ext_sigma",
  "ext_smooth_sigma",
  "ext_min_area",
  "ext_max_area",
  "ext_bin_factor",
  "ext_closing_iterations",
  "ext_opening_iterations",
  "ext_min_score",
  "ext_max_sources",
] as const;

export type PointDetectionParams = Pick<
  DetectSourcesParams,
  (typeof POINT_DETECTION_KEYS)[number]
>;

export type ExtendedDetectionParams = Pick<
  DetectSourcesParams,
  (typeof EXTENDED_DETECTION_KEYS)[number]
>;

export type SourceDetectionParams = Omit<DetectSourcesParams, "hdu">;

export const DEFAULT_POINT_DETECTION_PARAMS: PointDetectionParams = {
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

export const DEFAULT_EXTENDED_DETECTION_PARAMS: ExtendedDetectionParams = {
  ext_sigma: 3,
  ext_smooth_sigma: 8,
  ext_min_area: 500,
  ext_max_area: 0,
  ext_bin_factor: 8,
  ext_closing_iterations: 2,
  ext_opening_iterations: 1,
  ext_min_score: 0.2,
  ext_max_sources: 3,
};

export const DEFAULT_SOURCE_DETECTION_PARAMS: SourceDetectionParams = {
  ...DEFAULT_POINT_DETECTION_PARAMS,
  ...DEFAULT_EXTENDED_DETECTION_PARAMS,
};

export function pointDetectionParams(
  values: SourceDetectionParams,
): PointDetectionParams {
  const selected: Partial<PointDetectionParams> = {};
  for (const key of POINT_DETECTION_KEYS) {
    selected[key] = values[key];
  }
  return selected as PointDetectionParams;
}

export const POINT_DETECTION_PRESETS: NamedPreset<PointDetectionParams>[] = [
  {
    id: "equilibrio",
    label: "Equilibrio",
    outcome: "Las estrellas que se ven claro, un número manejable de marcas.",
    hint: "Primera detección.",
    values: DEFAULT_POINT_DETECTION_PARAMS,
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
