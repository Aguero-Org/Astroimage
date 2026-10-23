import { describe, expect, it } from "vitest";
import { simbadObjectTypeName } from "./simbad-object-types";

describe("simbadObjectTypeName", () => {
  it("maps known object type codes to Spanish names", () => {
    expect(simbadObjectTypeName("G", "Galaxy")).toBe("Galaxia");
    expect(simbadObjectTypeName("Be*", "Be*")).toBe("Estrella Be");
    expect(simbadObjectTypeName("PN", "PlanetaryNeb")).toBe(
      "Nebulosa planetaria",
    );
    expect(simbadObjectTypeName("*", "Star")).toBe("Estrella");
  });

  it("falls back to the SIMBAD text label when the code is unknown", () => {
    expect(simbadObjectTypeName("Foo*", "Foo Star")).toBe("Foo Star");
  });

  it("falls back to the raw code when no text is available", () => {
    expect(simbadObjectTypeName("Foo*", null)).toBe("Foo*");
  });

  it("returns null when there is no type at all", () => {
    expect(simbadObjectTypeName(null, null)).toBeNull();
  });
});
