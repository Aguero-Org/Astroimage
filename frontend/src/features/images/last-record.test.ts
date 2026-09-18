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
    expect(readLastImageRecord()).toBe("m31");
  });
});
