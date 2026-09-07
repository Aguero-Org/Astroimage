import { describe, expect, it } from "vitest";
import { CUSTOM_PRESET_ID, matchNamedPreset } from "./named-preset";

const PRESETS = [
  {
    id: "estandar",
    label: "Estándar",
    outcome: "ok",
    hint: "hint",
    values: { a: 1, b: "x" },
  },
] as const;

describe("matchNamedPreset", () => {
  it("returns the matching preset id", () => {
    expect(matchNamedPreset(PRESETS, { a: 1, b: "x" })).toBe("estandar");
  });

  it("returns custom when a field differs", () => {
    expect(matchNamedPreset(PRESETS, { a: 2, b: "x" })).toBe(CUSTOM_PRESET_ID);
  });
});
