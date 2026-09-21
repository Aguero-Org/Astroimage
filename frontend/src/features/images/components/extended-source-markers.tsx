import { useCoordinates, useViewerEvent } from "@cellbytes/react-openseadragon";
import { useState } from "react";
import type { ExtendedSourceSchema } from "@/api/generated/model";
import { cn } from "@/lib/utils";
import { FITS_RENDER_IMAGE_KEY } from "../source-detection";

type ExtendedSourceMarkersProps = {
  sources: ExtendedSourceSchema[];
  selectedId?: number | null;
  onSelect?: (source: ExtendedSourceSchema) => void;
};

export function ExtendedSourceMarkers({
  sources,
  selectedId = null,
  onSelect,
}: Readonly<ExtendedSourceMarkersProps>) {
  const coords = useCoordinates(FITS_RENDER_IMAGE_KEY);
  const [overlayVersion, setOverlayVersion] = useState(0);

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
    <ul
      className="pointer-events-none absolute inset-0 z-[4] overflow-hidden"
      data-testid="extended-source-overlay"
      data-overlay-version={overlayVersion}
    >
      {sources.map((source) => {
        const halfWidth = source.width_pixels / 2;
        const halfHeight = source.height_pixels / 2;
        const topLeft = coords.viewportToPixel(
          coords.imageToViewport(
            source.xcentroid - halfWidth,
            source.ycentroid - halfHeight,
          ),
        );
        const bottomRight = coords.viewportToPixel(
          coords.imageToViewport(
            source.xcentroid + halfWidth,
            source.ycentroid + halfHeight,
          ),
        );
        const width = bottomRight.x - topLeft.x;
        const height = bottomRight.y - topLeft.y;
        const selected = source.source_id === selectedId;
        const label = `Fuente extendida ${source.rank}, área ${source.area_pixels} px`;

        return (
          <li
            key={`extended-${source.source_id}`}
            className="absolute"
            style={{ left: topLeft.x, top: topLeft.y, width, height }}
          >
            <button
              type="button"
              data-testid="extended-source-marker"
              aria-label={label}
              aria-pressed={selected}
              title={label}
              className={cn(
                "pointer-events-auto size-full cursor-pointer rounded-sm border-2 bg-primary/15 shadow-sm",
                selected ? "border-accent" : "border-primary",
              )}
              onClick={() => {
                onSelect?.(source);
              }}
            />
          </li>
        );
      })}
    </ul>
  );
}
