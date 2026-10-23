import { afterEach, describe, expect, it, vi } from "vitest";
import {
  LAST_IMAGE_RECORD_KEY,
  readLastImageRecord,
  rememberLastImageRecord,
  subscribeLastImageRecord,
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

  it("keeps the persisted key and refreshes after the record is removed", () => {
    expect(LAST_IMAGE_RECORD_KEY).toBe("astroimage-last-record");

    rememberLastImageRecord("m31");
    expect(readLastImageRecord()).toEqual({ recordId: "m31" });

    sessionStorage.removeItem(LAST_IMAGE_RECORD_KEY);
    expect(readLastImageRecord()).toBeNull();
  });

  it("drops malformed or incomplete stored values", () => {
    sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, "{not-json");
    expect(readLastImageRecord()).toBeNull();

    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: 42 }),
    );
    expect(readLastImageRecord()).toBeNull();

    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: "" }),
    );
    expect(readLastImageRecord()).toBeNull();
  });

  it("omits an empty slug and keeps a record id without one", () => {
    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: "m31", slug: "" }),
    );
    expect(readLastImageRecord()).toEqual({ recordId: "m31" });

    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: "m42" }),
    );
    expect(readLastImageRecord()).toEqual({ recordId: "m42" });
  });

  it("notifies subscribers until they unsubscribe", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeLastImageRecord(listener);

    rememberLastImageRecord("m31");
    expect(listener).toHaveBeenCalledOnce();

    unsubscribe();
    rememberLastImageRecord("m42");
    expect(listener).toHaveBeenCalledOnce();
  });
});
