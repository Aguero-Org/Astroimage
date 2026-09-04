import { useCoordinates, useViewerEvent } from "@cellbytes/react-openseadragon";
import { useState } from "react";
import type { PointSourceSchema } from "@/api/generated/model";
import { FITS_RENDER_IMAGE_KEY } from "../source-detection";
import { SourceMarker } from "./source-marker";

type SourceMarkersProps = {
  sources: PointSourceSchema[];
};

export function SourceMarkers({ sources }: SourceMarkersProps) {
  const coords = useCoordinates(FITS_RENDER_IMAGE_KEY);
  const [, setOverlayVersion] = useState(0);

  function refreshOverlay() {
    setOverlayVersion((version) => version + 1);
  }

  useViewerEvent("animation", refreshOverlay);
  useViewerEvent("animation-finish", refreshOverlay);
  useViewerEvent("resize", refreshOverlay);

  if (!coords.tiledImage || sources.length === 0) {
    return null;
  }

  return (
    <ul className="pointer-events-none absolute inset-0 z-[5] overflow-hidden">
      {sources.map((source) => {
        const viewport = coords.imageToViewport(
          source.xcentroid,
          source.ycentroid,
        );
        const pixel = coords.viewportToPixel(viewport);
        return (
          <li
            key={source.source_id}
            className="absolute"
            style={{
              left: pixel.x,
              top: pixel.y,
              transform: "translate(-50%, -50%)",
            }}
          >
            <SourceMarker source={source} />
          </li>
        );
      })}
    </ul>
  );
}
