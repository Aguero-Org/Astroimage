import { describe, expect, it } from "vitest";
import { MOCK_POINT_SOURCE } from "@/mocks/data/image";
import {
  DEFAULT_IMAGE_WORKSPACE,
  imageWorkspaceReducer,
  resolveWorkspaceHdu,
} from "./image-workspace";
import { DEFAULT_RENDER_PARAMS } from "./render-view";
import { DEFAULT_SOURCE_DETECTION_PARAMS } from "./source-detection";

describe("ImageWorkspaceUi", () => {
  it("starts with empty selection and schema render/detection defaults", () => {
    expect(DEFAULT_IMAGE_WORKSPACE).toEqual({
      hdu: null,
      inspectorOpen: false,
      selectedSource: null,
      renderParams: DEFAULT_RENDER_PARAMS,
      detectionParams: DEFAULT_SOURCE_DETECTION_PARAMS,
    });
  });

  it("omits the hdu when the file has a single image plane", () => {
    expect(resolveWorkspaceHdu(1, [{ index: 1 }], 1)).toBeNull();
  });

  it("keeps a stored hdu that still exists on the file", () => {
    expect(resolveWorkspaceHdu(2, [{ index: 1 }, { index: 2 }], 1)).toBe(2);
  });

  it("falls back to the selected plane when the stored hdu is gone", () => {
    expect(resolveWorkspaceHdu(9, [{ index: 1 }, { index: 2 }], 1)).toBe(1);
  });

  it("falls back to the first plane when nothing was selected", () => {
    expect(resolveWorkspaceHdu(null, [{ index: 1 }, { index: 2 }], null)).toBe(
      1,
    );
  });

  it("opens and closes the inspector explicitly", () => {
    const open = imageWorkspaceReducer(DEFAULT_IMAGE_WORKSPACE, {
      type: "set-inspector-open",
      open: true,
    });
    expect(open).toEqual({ ...DEFAULT_IMAGE_WORKSPACE, inspectorOpen: true });

    const closed = imageWorkspaceReducer(open, {
      type: "set-inspector-open",
      open: false,
    });
    expect(closed).toEqual(DEFAULT_IMAGE_WORKSPACE);
  });

  it("stores render params without touching the selection", () => {
    const params = {
      ...DEFAULT_RENDER_PARAMS,
      stretch: "log" as const,
    };
    const selected = {
      ...DEFAULT_IMAGE_WORKSPACE,
      selectedSource: MOCK_POINT_SOURCE,
    };
    const next = imageWorkspaceReducer(selected, {
      type: "set-render-params",
      params,
    });

    expect(next.renderParams).toBe(params);
    expect(next.selectedSource).toBe(MOCK_POINT_SOURCE);
  });

  it("stores detection params and clears the selection", () => {
    const params = {
      ...DEFAULT_SOURCE_DETECTION_PARAMS,
      sigma: 4,
    };
    const selected = {
      ...DEFAULT_IMAGE_WORKSPACE,
      selectedSource: MOCK_POINT_SOURCE,
    };
    const next = imageWorkspaceReducer(selected, {
      type: "set-detection-params",
      params,
    });

    expect(next.detectionParams).toBe(params);
    expect(next.selectedSource).toBeNull();
  });

  it("selects a source and opens the inspector", () => {
    const next = imageWorkspaceReducer(DEFAULT_IMAGE_WORKSPACE, {
      type: "select-source",
      source: MOCK_POINT_SOURCE,
    });

    expect(next.selectedSource).toBe(MOCK_POINT_SOURCE);
    expect(next.inspectorOpen).toBe(true);
  });

  it("clears the selection when the hdu changes", () => {
    const selected = {
      ...DEFAULT_IMAGE_WORKSPACE,
      selectedSource: MOCK_POINT_SOURCE,
    };
    const next = imageWorkspaceReducer(selected, { type: "set-hdu", hdu: 2 });

    expect(next.hdu).toBe(2);
    expect(next.selectedSource).toBeNull();
  });
});
