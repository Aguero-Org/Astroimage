import { describe, expect, it } from "vitest";
import { humanizeImageSlug, imageDisplayTitle } from "./image-title";

describe("humanizeImageSlug", () => {
  it("uppercases words and drops the trailing content hash", () => {
    expect(humanizeImageSlug("m31-wfpc2-pc-37649737")).toBe("M31 WFPC2 PC");
    expect(humanizeImageSlug("ngc-5194-abcdef")).toBe("NGC 5194");
  });

  it("keeps short trailing digits that are not a hash", () => {
    expect(humanizeImageSlug("m42-12345")).toBe("M42 12345");
  });

  it("only strips a hash at the end of the slug", () => {
    expect(humanizeImageSlug("m31-abcdef-extra")).toBe("M31 ABCDEF EXTRA");
  });

  it("ignores empty segments", () => {
    expect(humanizeImageSlug("m--31")).toBe("M 31");
  });
});

describe("imageDisplayTitle", () => {
  it("uses a catalog name when the metadata has one", () => {
    expect(
      imageDisplayTitle("M31 - Andromeda Galaxy", "m31-wfc3-abcdef12"),
    ).toBe("M31 - Andromeda Galaxy");
  });

  it("trims the catalog name before using it", () => {
    expect(imageDisplayTitle("  M31  ", undefined)).toBe("M31");
  });

  it("humanizes the slug instead of a product filename or a uuid", () => {
    expect(
      imageDisplayTitle("u2kj0102t_drw.fits", "m31-wfpc2-pc-37649737"),
    ).toBe("M31 WFPC2 PC");
    expect(imageDisplayTitle(undefined, "m31-wfpc2-pc-37649737")).toBe(
      "M31 WFPC2 PC",
    );
  });

  it("treats UUIDs only as exact technical names", () => {
    const uuid = "12345678-1234-1234-1234-123456789abc";
    const malformed = [
      `prefix-${uuid}`,
      `${uuid}-extra`,
      "a-1234-1234-1234-123456789abc",
      "zzzzzzzz-1234-1234-1234-123456789abc",
      "12345678-a-1234-1234-123456789abc",
      "12345678-zzzz-1234-1234-123456789abc",
      "12345678-1234-a-1234-123456789abc",
      "12345678-1234-zzzz-1234-123456789abc",
      "12345678-1234-1234-a-123456789abc",
      "12345678-1234-1234-zzzz-123456789abc",
      "12345678-1234-1234-1234-a",
      "12345678-1234-1234-1234-zzzzzzzzzzzz",
    ];

    expect(imageDisplayTitle(uuid, "m31-abcdef12")).toBe("M31");
    malformed.forEach((name) => {
      expect(imageDisplayTitle(name, "m31-abcdef12")).toBe(name);
    });
  });

  it("falls back to the trimmed filename without its extension", () => {
    expect(imageDisplayTitle("u2kj0102t_drw.fits", undefined)).toBe(
      "u2kj0102t_drw",
    );
    expect(imageDisplayTitle("image.FIT", undefined)).toBe("image");
    expect(imageDisplayTitle("image.fits.gz", undefined)).toBe("image.fits.gz");
    expect(imageDisplayTitle("image.fits.gz", "m31-abcdef12")).toBe(
      "image.fits.gz",
    );
    expect(imageDisplayTitle("a.fits.b.fits", undefined)).toBe("a.fits.b");
  });

  it("falls back to Imagen when there is nothing usable", () => {
    expect(imageDisplayTitle(undefined, undefined)).toBe("Imagen");
    expect(imageDisplayTitle(null, "---")).toBe("Imagen");
    expect(imageDisplayTitle("   ", "  ")).toBe("Imagen");
  });
});
