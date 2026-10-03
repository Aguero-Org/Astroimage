import type {
  ExtendedDetectionConfigSchema,
  PointDetectionConfigSchema,
  PresetEvidenceSchema,
  SourcePresetResponse,
} from "@/api/generated/model";
import type {
  ExtendedDetectionParams,
  PointDetectionParams,
} from "./source-detection";
import {
  DEFAULT_EXTENDED_DETECTION_PARAMS,
  DEFAULT_POINT_DETECTION_PARAMS,
} from "./source-detection";

/**
 * The preset endpoint answers with the values the user already had plus the
 * ones rescaled from the measured PSF. A missing field means "keep what you
 * have", so a partial answer never wipes what the user typed.
 */
export type BestPreset = {
  isPending: boolean;
  isError: boolean;
  data: SourcePresetResponse | undefined;
  request: () => void;
};

export const NO_MEASUREMENT_SUMMARY =
  "No se pudo medir el núcleo en esta imagen: quedan los valores que ya tenías.";

export function bestPresetPointParams(
  preset: SourcePresetResponse,
  current: PointDetectionParams,
): PointDetectionParams {
  const config: PointDetectionConfigSchema = preset.point_config;
  const base = { ...DEFAULT_POINT_DETECTION_PARAMS, ...current };
  return {
    fwhm: config.fwhm ?? base.fwhm,
    sigma: config.sigma ?? base.sigma,
    min_snr: config.min_snr ?? base.min_snr,
    min_score: config.min_score ?? base.min_score,
    min_distance: config.min_distance ?? base.min_distance,
    visual_weight: config.visual_weight ?? base.visual_weight,
    visual_area_radius: config.visual_area_radius ?? base.visual_area_radius,
    visual_area_sigma: config.visual_area_sigma ?? base.visual_area_sigma,
    max_sources: Math.round(config.max_sources ?? base.max_sources),
  };
}

export function bestPresetExtendedParams(
  preset: SourcePresetResponse,
  current: ExtendedDetectionParams,
): ExtendedDetectionParams {
  const config: ExtendedDetectionConfigSchema = preset.extended_config;
  const base = { ...DEFAULT_EXTENDED_DETECTION_PARAMS, ...current };
  return {
    ext_sigma: config.sigma ?? base.ext_sigma,
    ext_smooth_sigma: config.smooth_sigma ?? base.ext_smooth_sigma,
    ext_min_area: Math.round(config.min_area ?? base.ext_min_area),
    ext_max_area: Math.round(config.max_area ?? base.ext_max_area),
    ext_bin_factor: Math.round(config.bin_factor ?? base.ext_bin_factor),
    ext_closing_iterations: Math.round(
      config.closing_iterations ?? base.ext_closing_iterations,
    ),
    ext_opening_iterations: Math.round(
      config.opening_iterations ?? base.ext_opening_iterations,
    ),
    ext_min_score: config.min_score ?? base.ext_min_score,
    ext_max_sources: Math.round(config.max_sources ?? base.ext_max_sources),
  };
}

/** One line saying what the measurement was based on, or why there is none. */
export function bestPresetSummary(evidence?: PresetEvidenceSchema): string {
  const measured = evidence?.measured_fwhm;
  const samples = evidence?.fwhm_samples ?? 0;
  if (measured === undefined || measured === null || samples < 1) {
    return NO_MEASUREMENT_SUMMARY;
  }
  const spread = evidence?.fwhm_spread;
  const spreadText =
    spread === undefined || spread === null
      ? ""
      : `, dispersión ${spread.toFixed(1)} px`;
  return `Medido en esta imagen: FWHM ${measured.toFixed(1)} px sobre ${samples} ${samples === 1 ? "fuente" : "fuentes"}${spreadText}.`;
}
