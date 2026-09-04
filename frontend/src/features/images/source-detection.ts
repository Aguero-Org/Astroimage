import type { DetectSourcesParams } from "@/api/generated/model";

export const DEFAULT_SOURCE_DETECTION_PARAMS: Omit<DetectSourcesParams, "hdu"> =
  {
    fwhm: 5.5,
    sigma: 9,
    min_snr: 6,
    min_score: 0.18,
    min_distance: 4,
    visual_weight: 0.8,
    visual_area_radius: 7,
    visual_area_sigma: 2,
    max_sources: 50,
    extended_min_snr: 0,
    extended_max_sources: 50,
  };

export const FITS_RENDER_IMAGE_KEY = "fits-render";
