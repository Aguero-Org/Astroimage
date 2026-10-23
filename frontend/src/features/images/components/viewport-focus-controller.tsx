import { useCoordinates, useViewer } from "@cellbytes/react-openseadragon";
import { useEffect } from "react";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { FITS_RENDER_IMAGE_KEY } from "../fits-render-image-key";

export type ImageFocusRequest = {
  requestId: number;
  source: PointSourceSchema | ExtendedSourceSchema;
};

type ViewportFocusControllerProps = {
  request?: ImageFocusRequest | null;
};

const MIN_FOCUS_SIZE_PX = 24;
const MAX_FOCUS_SIZE_PX = 160;

export function ViewportFocusController({
  request,
}: Readonly<ViewportFocusControllerProps>) {
  const { viewer } = useViewer();
  const coords = useCoordinates(FITS_RENDER_IMAGE_KEY);

  useEffect(() => {
    if (!request || !viewer || !coords.tiledImage) {
      return;
    }
    const content = coords.tiledImage.getContentSize();
    const baseSize = Math.max(
      MIN_FOCUS_SIZE_PX,
      Math.min(MAX_FOCUS_SIZE_PX, Math.min(content.x, content.y) / 8),
    );
    const { source } = request;
    const width =
      source.object_type === "extended"
        ? Math.max(baseSize, source.width_pixels * 1.5)
        : baseSize;
    const height =
      source.object_type === "extended"
        ? Math.max(baseSize, source.height_pixels * 1.5)
        : baseSize;
    const bounds = coords.imageToViewportRect(
      source.xcentroid - width / 2,
      source.ycentroid - height / 2,
      width,
      height,
    );
    viewer.viewport.fitBounds(bounds);
  }, [coords, request, viewer]);

  return null;
}
