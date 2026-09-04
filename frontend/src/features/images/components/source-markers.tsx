import { useCoordinates, useViewerEvent } from "@cellbytes/react-openseadragon";
import { useState } from "react";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { FITS_RENDER_IMAGE_KEY } from "../source-detection";
import { SourceMarker } from "./source-marker";

type SourceMarkersProps = {
  sources: PointSourceSchema[];
  extendedSources?: ExtendedSourceSchema[];
};

type MarkerEntry = {
  key: string;
  source: {
    xcentroid: number;
    ycentroid: number;
    snr: number;
    rank: number;
    object_type?: string;
  };
};

function toMarkerEntries(
  points: PointSourceSchema[],
  extended: ExtendedSourceSchema[],
): MarkerEntry[] {
  const entries: MarkerEntry[] = [];
  for (const s of points) {
    entries.push({
      key: `point-${s.source_id}`,
      source: s,
    });
  }
  for (const s of extended) {
    entries.push({
      key: `extended-${s.source_id}`,
      source: s,
    });
  }
  return entries;
}

export function SourceMarkers({
  sources,
  extendedSources = [],
}: SourceMarkersProps) {
  const coords = useCoordinates(FITS_RENDER_IMAGE_KEY);
  const [, setOverlayVersion] = useState(0);
  const entries = toMarkerEntries(sources, extendedSources);

  function refreshOverlay() {
    setOverlayVersion((version) => version + 1);
  }

  useViewerEvent("animation", refreshOverlay);
  useViewerEvent("animation-finish", refreshOverlay);
  useViewerEvent("resize", refreshOverlay);

  if (!coords.tiledImage || entries.length === 0) {
    return null;
  }

  return (
    <ul className="pointer-events-none absolute inset-0 z-[5] overflow-hidden">
      {entries.map((entry) => {
        const viewport = coords.imageToViewport(
          entry.source.xcentroid,
          entry.source.ycentroid,
        );
        const pixel = coords.viewportToPixel(viewport);
        return (
          <li
            key={entry.key}
            className="absolute"
            style={{
              left: pixel.x,
              top: pixel.y,
              transform: "translate(-50%, -50%)",
            }}
          >
            <SourceMarker source={entry.source} />
          </li>
        );
      })}
    </ul>
  );
}
