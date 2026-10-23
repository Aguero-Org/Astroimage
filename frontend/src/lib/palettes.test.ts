import { describe, expect, it } from "vitest";
import {
  applyPalette,
  isPaletteId,
  PALETTE_STORAGE_KEY,
  PALETTES,
} from "./palettes";

describe("palettes", () => {
  it("keeps the persisted key stable", () => {
    expect(PALETTE_STORAGE_KEY).toBe("astroimage-palette");
  });

  it("applies five swatches to CSS variables", () => {
    applyPalette("cosmic");
    const styles = document.documentElement.style;
    PALETTES.cosmic.swatches.forEach((hex, index) => {
      expect(styles.getPropertyValue(`--palette-${index + 1}`)).toBe(hex);
    });
  });

  it("accepts known palette ids only", () => {
    expect(isPaletteId("cosmic")).toBe(true);
    expect(isPaletteId("nope")).toBe(false);
    expect(isPaletteId(null)).toBe(false);
  });
});
