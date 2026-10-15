import { describe, expect, it } from "vitest";
import {
  DEFAULT_IMAGE_WORKSPACE,
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
});
