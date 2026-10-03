import { describe, expect, it } from "vitest";
import type { SourcePresetResponse } from "@/api/generated/model";
import {
  bestPresetExtendedParams,
  bestPresetPointParams,
  bestPresetSummary,
  NO_MEASUREMENT_SUMMARY,
} from "./best-preset";
import {
  DEFAULT_EXTENDED_DETECTION_PARAMS,
  DEFAULT_POINT_DETECTION_PARAMS,
} from "./source-detection";

function preset(
  overrides: Partial<SourcePresetResponse> = {},
): SourcePresetResponse {
  return {
    point_config: {},
    extended_config: {},
    baseline_point_config: {},
    baseline_extended_config: {},
    ...overrides,
  };
}

describe("bestPresetPointParams", () => {
  it("takes the measured point values", () => {
    const next = bestPresetPointParams(
      preset({ point_config: { fwhm: 9.5, min_distance: 8 } }),
      DEFAULT_POINT_DETECTION_PARAMS,
    );

    expect(next.fwhm).toBe(9.5);
    expect(next.min_distance).toBe(8);
  });

  it("keeps the current value for every field the answer omits", () => {
    const next = bestPresetPointParams(
      preset({ point_config: { fwhm: 9.5 } }),
      DEFAULT_POINT_DETECTION_PARAMS,
    );

    expect(next).toEqual({ ...DEFAULT_POINT_DETECTION_PARAMS, fwhm: 9.5 });
  });

  it("keeps the values the user typed instead of the defaults", () => {
    const typed = { ...DEFAULT_POINT_DETECTION_PARAMS, min_snr: 42, sigma: 3 };
    const next = bestPresetPointParams(preset({ point_config: {} }), typed);

    expect(next.min_snr).toBe(42);
    expect(next.sigma).toBe(3);
  });

  it("rounds the source cap", () => {
    const next = bestPresetPointParams(
      preset({ point_config: { max_sources: 50.6 } }),
      DEFAULT_POINT_DETECTION_PARAMS,
    );

    expect(next.max_sources).toBe(51);
  });
});

describe("bestPresetExtendedParams", () => {
  it("maps the extended fields onto their form keys", () => {
    const next = bestPresetExtendedParams(
      preset({
        extended_config: { sigma: 6, smooth_sigma: 16, min_area: 800 },
      }),
      DEFAULT_EXTENDED_DETECTION_PARAMS,
    );

    expect(next.ext_sigma).toBe(6);
    expect(next.ext_smooth_sigma).toBe(16);
    expect(next.ext_min_area).toBe(800);
  });

  it("keeps the current value for omitted fields", () => {
    const next = bestPresetExtendedParams(
      preset({ extended_config: { smooth_sigma: 16 } }),
      DEFAULT_EXTENDED_DETECTION_PARAMS,
    );

    expect(next).toEqual({
      ...DEFAULT_EXTENDED_DETECTION_PARAMS,
      ext_smooth_sigma: 16,
    });
  });

  it("rounds the integer fields", () => {
    const next = bestPresetExtendedParams(
      preset({
        extended_config: {
          min_area: 800.4,
          bin_factor: 7.6,
          closing_iterations: 2.2,
          max_sources: 4.5,
        },
      }),
      DEFAULT_EXTENDED_DETECTION_PARAMS,
    );

    expect(next.ext_min_area).toBe(800);
    expect(next.ext_bin_factor).toBe(8);
    expect(next.ext_closing_iterations).toBe(2);
    expect(next.ext_max_sources).toBe(5);
  });
});

describe("bestPresetSummary", () => {
  it("reports the measured width and how many sources it used", () => {
    const text = bestPresetSummary({
      measured_fwhm: 8.34,
      fwhm_samples: 12,
      fwhm_spread: 1.24,
    });

    expect(text).toBe(
      "Medido en esta imagen: FWHM 8.3 px sobre 12 fuentes, dispersión 1.2 px.",
    );
  });

  it("uses the singular for a single source", () => {
    expect(bestPresetSummary({ measured_fwhm: 4, fwhm_samples: 1 })).toContain(
      "sobre 1 fuente.",
    );
  });

  it("omits the spread when the answer has none", () => {
    expect(
      bestPresetSummary({ measured_fwhm: 4, fwhm_samples: 3 }),
    ).not.toContain("dispersión");
  });

  it("explains the fallback when nothing could be measured", () => {
    expect(bestPresetSummary(undefined)).toBe(NO_MEASUREMENT_SUMMARY);
    expect(bestPresetSummary({})).toBe(NO_MEASUREMENT_SUMMARY);
    expect(bestPresetSummary({ measured_fwhm: null, fwhm_samples: 0 })).toBe(
      NO_MEASUREMENT_SUMMARY,
    );
  });
});
