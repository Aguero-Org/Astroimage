import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  LAST_IMAGE_RECORD_KEY,
  rememberLastImageRecord,
  useLastRecordStore,
} from "./last-record";

function resetStore(): void {
  sessionStorage.removeItem(LAST_IMAGE_RECORD_KEY);
  useLastRecordStore.setState({ record: null });
}

describe("useLastRecordStore", () => {
  beforeEach(resetStore);
  afterEach(resetStore);

  it("keeps the persisted key", () => {
    expect(LAST_IMAGE_RECORD_KEY).toBe("astroimage-last-record");
  });

  it("updates state and writes the raw record JSON", () => {
    expect(useLastRecordStore.getState().record).toBeNull();

    rememberLastImageRecord("m31");

    expect(useLastRecordStore.getState().record).toEqual({ recordId: "m31" });
    expect(sessionStorage.getItem(LAST_IMAGE_RECORD_KEY)).toBe(
      '{"recordId":"m31"}',
    );
  });

  it("keeps the slug and omits an empty one", () => {
    rememberLastImageRecord("m31", "hst_123.fits");

    expect(useLastRecordStore.getState().record).toEqual({
      recordId: "m31",
      slug: "hst_123.fits",
    });
    expect(sessionStorage.getItem(LAST_IMAGE_RECORD_KEY)).toBe(
      '{"recordId":"m31","slug":"hst_123.fits"}',
    );

    rememberLastImageRecord("m42", "");

    expect(useLastRecordStore.getState().record).toEqual({ recordId: "m42" });
    expect(sessionStorage.getItem(LAST_IMAGE_RECORD_KEY)).toBe(
      '{"recordId":"m42"}',
    );
  });

  it("clears the record and removes the stored key", () => {
    rememberLastImageRecord("m31");

    useLastRecordStore.getState().clear();

    expect(useLastRecordStore.getState().record).toBeNull();
    expect(sessionStorage.getItem(LAST_IMAGE_RECORD_KEY)).toBeNull();
  });

  it("rehydrates a legacy plain record id", async () => {
    sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, "m31");

    await useLastRecordStore.persist.rehydrate();

    expect(useLastRecordStore.getState().record).toEqual({ recordId: "m31" });
  });

  it("rehydrates a raw legacy record and drops an empty slug", async () => {
    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: "m31", slug: "hst_123.fits" }),
    );

    await useLastRecordStore.persist.rehydrate();

    expect(useLastRecordStore.getState().record).toEqual({
      recordId: "m31",
      slug: "hst_123.fits",
    });

    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: "m42", slug: "" }),
    );

    await useLastRecordStore.persist.rehydrate();

    expect(useLastRecordStore.getState().record).toEqual({ recordId: "m42" });
  });

  it("drops malformed or incomplete stored values", async () => {
    sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, "{not-json");
    await useLastRecordStore.persist.rehydrate();
    expect(useLastRecordStore.getState().record).toBeNull();

    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: 42 }),
    );
    await useLastRecordStore.persist.rehydrate();
    expect(useLastRecordStore.getState().record).toBeNull();

    sessionStorage.setItem(
      LAST_IMAGE_RECORD_KEY,
      JSON.stringify({ recordId: "" }),
    );
    await useLastRecordStore.persist.rehydrate();
    expect(useLastRecordStore.getState().record).toBeNull();
  });
});
