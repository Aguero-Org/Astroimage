import { useCoordinates, useViewerEvent } from "@cellbytes/react-openseadragon";
import { useState } from "react";
import type { ExtendedSourceSchema } from "@/api/generated/model";
import { cn } from "@/lib/utils";
import { FITS_RENDER_IMAGE_KEY } from "../fits-render-image-key";
import {
  type SourceFocusPulse,
  sourceFocusPulseKey,
} from "../source-focus-pulse";
import { SimbadMatchBadge } from "./simbad-match-badge";

function extendedFace(simbadMatch: boolean, gaiaMatch: boolean): string {
  if (simbadMatch) {
    return "border-simbad bg-simbad/20";
  }
  if (gaiaMatch) {
    return "border-gaia bg-gaia/20";
  }
  return "border-amber-300 bg-amber-300/20";
}

function extendedRing(
  selected: boolean,
  simbadMatch: boolean,
  gaiaMatch: boolean,
): string {
  if (selected) {
    return "ring-accent";
  }
  if (simbadMatch) {
    return "ring-simbad";
  }
  if (gaiaMatch) {
    return "ring-gaia";
  }
  return "ring-background";
}

type ExtendedSourceMarkersProps = {
  sources: ExtendedSourceSchema[];
  selectedId?: number | null;
  gaiaMatchedIds?: ReadonlySet<number>;
  simbadMatchedIds?: ReadonlySet<number>;
  focusPulse?: SourceFocusPulse | null;
  onSelect?: (source: ExtendedSourceSchema) => void;
};

export function ExtendedSourceMarkers({
  sources,
  selectedId = null,
  gaiaMatchedIds,
  simbadMatchedIds,
  focusPulse,
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
        const gaiaMatch = gaiaMatchedIds?.has(source.source_id) ?? false;
        const simbadMatch = simbadMatchedIds?.has(source.source_id) ?? false;
        const label = `Fuente extendida ${source.rank}, área ${source.area_pixels} px${simbadMatch ? ", SIMBAD" : ""}`;

        return (
          <li
            key={`extended-${source.source_id}`}
            className="absolute"
            style={{ left: topLeft.x, top: topLeft.y, width, height }}
          >
            <button
              key={sourceFocusPulseKey(
                focusPulse,
                source.source_id,
                "extended",
              )}
              type="button"
              data-testid="extended-source-marker"
              aria-label={label}
              aria-pressed={selected}
              data-gaia-match={gaiaMatch ? "true" : "false"}
              data-simbad-match={simbadMatch ? "true" : "false"}
              title={label}
              className={cn(
                "pointer-events-auto absolute left-1/2 top-1/2 h-full w-full -translate-x-1/2 -translate-y-1/2 cursor-pointer rounded-sm border-2 shadow-sm ring-2",
                extendedFace(simbadMatch, gaiaMatch),
                extendedRing(selected, simbadMatch, gaiaMatch),
                sourceFocusPulseKey(
                  focusPulse,
                  source.source_id,
                  "extended",
                ) !== undefined && "source-focus-pulse",
              )}
              onClick={() => {
                onSelect?.(source);
              }}
            >
              {simbadMatch ? (
                <SimbadMatchBadge className="-top-2 -left-2" />
              ) : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
