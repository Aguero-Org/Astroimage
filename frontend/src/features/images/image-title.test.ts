import { describe, expect, it } from "vitest";
import { imageDisplayTitle } from "./image-title";

describe("imageDisplayTitle", () => {
  it("uses a catalog name when the metadata has one", () => {
    expect(
      imageDisplayTitle("M31 - Andromeda Galaxy", "m31-wfc3-abcdef12"),
    ).toBe("M31 - Andromeda Galaxy");
  });

  it("humanizes the slug instead of a product filename or a uuid", () => {
    expect(
      imageDisplayTitle("u2kj0102t_drw.fits", "m31-wfpc2-pc-37649737"),
    ).toBe("M31 WFPC2 PC");
    expect(imageDisplayTitle(undefined, "m31-wfpc2-pc-37649737")).toBe(
      "M31 WFPC2 PC",
    );
  });
});
