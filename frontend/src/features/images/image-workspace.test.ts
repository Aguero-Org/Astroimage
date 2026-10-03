import { describe, expect, it } from "vitest";
import { DEFAULT_IMAGE_WORKSPACE } from "./image-workspace";
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
});
