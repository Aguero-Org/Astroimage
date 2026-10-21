import { act, renderHook } from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { LAST_IMAGE_RECORD_KEY, rememberLastImageRecord } from "./last-record";
import { useLastImageRecord } from "./use-last-image-record";

function ServerProbe() {
  const record = useLastImageRecord();
  return <span>{record === null ? "sin registro" : record.recordId}</span>;
}

describe("useLastImageRecord", () => {
  it("uses a null server snapshot", () => {
    expect(renderToString(<ServerProbe />)).toContain("sin registro");
  });

  afterEach(() => {
    sessionStorage.removeItem(LAST_IMAGE_RECORD_KEY);
  });

  it("returns the stored record and follows later changes", () => {
    const { result } = renderHook(() => useLastImageRecord());

    expect(result.current).toBeNull();

    act(() => {
      rememberLastImageRecord("m31", "hst_123.fits");
    });

    expect(result.current).toEqual({
      recordId: "m31",
      slug: "hst_123.fits",
    });
  });
});
