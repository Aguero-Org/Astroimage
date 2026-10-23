import {
  useCoordinates,
  useViewer,
  useViewerEvent,
} from "@cellbytes/react-openseadragon";
import { useCallback, useEffect, useRef } from "react";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { sourceKey } from "@/lib/source-key";
import { FITS_RENDER_IMAGE_KEY } from "../fits-render-image-key";

type ViewportBounds = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type Point = {
  x: number;
  y: number;
};

type ViewportSourceVisibilityProps = {
  pointSources: PointSourceSchema[];
  extendedSources: ExtendedSourceSchema[];
  onVisibleSourceKeysChange?: (keys: ReadonlySet<string>) => void;
};

export function visibleSourceKeys(
  pointSources: readonly PointSourceSchema[],
  extendedSources: readonly ExtendedSourceSchema[],
  bounds: ViewportBounds,
  imageToViewport: (x: number, y: number) => Point,
): ReadonlySet<string> {
  const keys = new Set<string>();

  for (const source of pointSources) {
    if (contains(bounds, imageToViewport(source.xcentroid, source.ycentroid))) {
      keys.add(sourceKey("point", source.source_id));
    }
  }

  for (const source of extendedSources) {
    const halfWidth = source.width_pixels / 2;
    const halfHeight = source.height_pixels / 2;
    const topLeft = imageToViewport(
      source.xcentroid - halfWidth,
      source.ycentroid - halfHeight,
    );
    const bottomRight = imageToViewport(
      source.xcentroid + halfWidth,
      source.ycentroid + halfHeight,
    );
    if (
      intersects(bounds, {
        x: Math.min(topLeft.x, bottomRight.x),
        y: Math.min(topLeft.y, bottomRight.y),
        width: Math.abs(bottomRight.x - topLeft.x),
        height: Math.abs(bottomRight.y - topLeft.y),
      })
    ) {
      keys.add(sourceKey("extended", source.source_id));
    }
  }

  return keys;
}

export function ViewportSourceVisibility({
  pointSources,
  extendedSources,
  onVisibleSourceKeysChange,
}: Readonly<ViewportSourceVisibilityProps>) {
  const { viewer } = useViewer();
  const coords = useCoordinates(FITS_RENDER_IMAGE_KEY);
  const lastSignature = useRef<string | null>(null);

  const reportVisibleSources = useCallback(() => {
    if (!viewer || !coords.tiledImage || !onVisibleSourceKeysChange) {
      return;
    }
    const keys = visibleSourceKeys(
      pointSources,
      extendedSources,
      viewer.viewport.getBounds(),
      coords.imageToViewport,
    );
    const signature = [...keys].sort().join("|");
    if (signature === lastSignature.current) {
      return;
    }
    lastSignature.current = signature;
    onVisibleSourceKeysChange(keys);
  }, [
    coords,
    extendedSources,
    onVisibleSourceKeysChange,
    pointSources,
    viewer,
  ]);

  useViewerEvent("animation-finish", reportVisibleSources);
  useViewerEvent("resize", reportVisibleSources);

  useEffect(() => {
    reportVisibleSources();
  }, [reportVisibleSources]);

  return null;
}

function contains(bounds: ViewportBounds, point: Point): boolean {
  return (
    point.x >= bounds.x &&
    point.x <= bounds.x + bounds.width &&
    point.y >= bounds.y &&
    point.y <= bounds.y + bounds.height
  );
}

function intersects(a: ViewportBounds, b: ViewportBounds): boolean {
  return (
    a.x <= b.x + b.width &&
    a.x + a.width >= b.x &&
    a.y <= b.y + b.height &&
    a.y + a.height >= b.y
  );
}
