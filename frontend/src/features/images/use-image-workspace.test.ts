import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MOCK_POINT_SOURCE } from "@/mocks/data/image";
import { useImageWorkspace } from "./use-image-workspace";

describe("useImageWorkspace", () => {
  it("dispatches selection actions through the reducer", () => {
    const { result } = renderHook(() => useImageWorkspace());

    act(() => {
      result.current[1]({ type: "select-source", source: MOCK_POINT_SOURCE });
    });

    expect(result.current[0].selectedSource).toBe(MOCK_POINT_SOURCE);
    expect(result.current[0].inspectorOpen).toBe(true);
  });
});
