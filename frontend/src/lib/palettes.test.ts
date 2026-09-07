import { describe, expect, it } from "vitest";
import { applyPalette, PALETTES } from "./palettes";

describe("palettes", () => {
  it("applies five swatches to CSS variables", () => {
    applyPalette("nebula");
    const styles = document.documentElement.style;
    PALETTES.nebula.swatches.forEach((hex, index) => {
      expect(styles.getPropertyValue(`--palette-${index + 1}`)).toBe(hex);
    });
  });
});
