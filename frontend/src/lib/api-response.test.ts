import { describe, expect, it } from "vitest";
import { okData } from "./api-response";

describe("okData", () => {
  it("returns the data of a successful response", () => {
    expect(okData({ status: 200, data: { value: 1 } })).toEqual({ value: 1 });
    expect(okData({ status: 200, data: 0 })).toBe(0);
  });

  it("returns undefined for missing or unsuccessful responses", () => {
    expect(okData(undefined)).toBeUndefined();
    expect(okData({ status: 204, data: { value: 1 } })).toBeUndefined();
    expect(okData({ status: 500, data: null })).toBeUndefined();
  });
});
