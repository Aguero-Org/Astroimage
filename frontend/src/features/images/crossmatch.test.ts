import { describe, expect, it } from "vitest";
import {
  crossmatchToDraft,
  DEFAULT_CROSSMATCH_PARAMS,
  parseCrossmatchDraft,
} from "./crossmatch";

describe("crossmatch params", () => {
  it("defaults Gaia and SIMBAD to five arcsec and power two", () => {
    expect(DEFAULT_CROSSMATCH_PARAMS).toEqual({
      gaiaRadiusArcsec: 5,
      gaiaProbabilityPower: 2,
      simbadRadiusArcsec: 5,
      simbadProbabilityPower: 2,
    });
  });

  it("round trips values through the draft", () => {
    const params = {
      gaiaRadiusArcsec: 7.5,
      gaiaProbabilityPower: 1.5,
      simbadRadiusArcsec: 4.25,
      simbadProbabilityPower: 3,
    };

    expect(parseCrossmatchDraft(crossmatchToDraft(params))).toEqual(params);
  });

  it("accepts the radius and power boundaries", () => {
    expect(
      parseCrossmatchDraft({
        gaiaRadius: "0",
        gaiaPower: "0.1",
        simbadRadius: "3600",
        simbadPower: "10",
      }),
    ).toEqual({
      gaiaRadiusArcsec: 0,
      gaiaProbabilityPower: 0.1,
      simbadRadiusArcsec: 3600,
      simbadProbabilityPower: 10,
    });
  });

  it("rejects a radius below zero", () => {
    expect(
      parseCrossmatchDraft({
        gaiaRadius: "-1",
        gaiaPower: "2",
        simbadRadius: "5",
        simbadPower: "2",
      }),
    ).toBeNull();
  });

  it("rejects a radius above the endpoint maximum", () => {
    expect(
      parseCrossmatchDraft({
        gaiaRadius: "5",
        gaiaPower: "2",
        simbadRadius: "3601",
        simbadPower: "2",
      }),
    ).toBeNull();
  });

  it("rejects probability powers below the endpoint minimum", () => {
    expect(
      parseCrossmatchDraft({
        gaiaRadius: "5",
        gaiaPower: "0.05",
        simbadRadius: "5",
        simbadPower: "2",
      }),
    ).toBeNull();
  });

  it("rejects blank and non numeric values", () => {
    expect(
      parseCrossmatchDraft({
        gaiaRadius: "",
        gaiaPower: "2",
        simbadRadius: "5",
        simbadPower: "2",
      }),
    ).toBeNull();
    expect(
      parseCrossmatchDraft({
        gaiaRadius: "5",
        gaiaPower: "dos",
        simbadRadius: "5",
        simbadPower: "2",
      }),
    ).toBeNull();
  });
});
