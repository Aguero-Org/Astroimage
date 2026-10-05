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

export const DEFAULT_IMAGE_WORKSPACE: ImageWorkspaceUi = {
  hdu: null,
  inspectorOpen: false,
  selectedSource: null,
  renderParams: DEFAULT_RENDER_PARAMS,
  detectionParams: DEFAULT_SOURCE_DETECTION_PARAMS,
};

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
