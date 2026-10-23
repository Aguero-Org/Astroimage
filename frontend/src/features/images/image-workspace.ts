import type {
  DetectSourcesParams,
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { DEFAULT_RENDER_PARAMS, type RenderViewParams } from "./render-view";
import { DEFAULT_SOURCE_DETECTION_PARAMS } from "./source-detection";

export type ImageWorkspaceUi = {
  hdu: number | null;
  inspectorOpen: boolean;
  selectedSource: PointSourceSchema | ExtendedSourceSchema | null;
  renderParams: RenderViewParams;
  detectionParams: DetectSourcesParams;
};

export type ImageWorkspaceAction =
  | { type: "set-inspector-open"; open: boolean }
  | {
      type: "select-source";
      source: PointSourceSchema | ExtendedSourceSchema;
    }
  | { type: "set-hdu"; hdu: number | null }
  | { type: "set-render-params"; params: RenderViewParams }
  | { type: "set-detection-params"; params: DetectSourcesParams };

export const DEFAULT_IMAGE_WORKSPACE: ImageWorkspaceUi = {
  hdu: null,
  inspectorOpen: false,
  selectedSource: null,
  renderParams: DEFAULT_RENDER_PARAMS,
  detectionParams: DEFAULT_SOURCE_DETECTION_PARAMS,
};

export function imageWorkspaceReducer(
  state: ImageWorkspaceUi,
  action: ImageWorkspaceAction,
): ImageWorkspaceUi {
  switch (action.type) {
    case "set-inspector-open":
      return { ...state, inspectorOpen: action.open };
    case "select-source":
      return {
        ...state,
        selectedSource: action.source,
        inspectorOpen: true,
      };
    case "set-hdu":
      return {
        ...state,
        hdu: action.hdu,
        selectedSource: null,
      };
    case "set-render-params":
      return { ...state, renderParams: action.params };
    case "set-detection-params":
      return {
        ...state,
        detectionParams: action.params,
        selectedSource: null,
      };
  }
}

export function resolveWorkspaceHdu(
  storedHdu: number | null,
  images: readonly { index: number }[],
  selectedHdu: number | null,
): number | null {
  if (images.length <= 1) {
    return null;
  }
  if (storedHdu !== null && images.some((plane) => plane.index === storedHdu)) {
    return storedHdu;
  }
  return selectedHdu ?? images[0]?.index ?? null;
}
