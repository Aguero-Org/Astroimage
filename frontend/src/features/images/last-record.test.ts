import { afterEach, describe, expect, it } from "vitest";
import {
  LAST_IMAGE_RECORD_KEY,
  readLastImageRecord,
  rememberLastImageRecord,
} from "./last-record";

describe("last image record", () => {
  afterEach(() => {
    sessionStorage.removeItem(LAST_IMAGE_RECORD_KEY);
  });

  it("stores and reads the last opened record", () => {
    expect(readLastImageRecord()).toBeNull();
    rememberLastImageRecord("m31");
    expect(readLastImageRecord()).toEqual({ recordId: "m31" });
  });

  it("keeps the slug used in the image link", () => {
    rememberLastImageRecord("m31", "hst_123.fits");
    expect(readLastImageRecord()).toEqual({
      recordId: "m31",
      slug: "hst_123.fits",
    });
  });

  it("reads a record id stored before slugs existed", () => {
    sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, "m31");
    expect(readLastImageRecord()).toEqual({ recordId: "m31" });
  });
});
