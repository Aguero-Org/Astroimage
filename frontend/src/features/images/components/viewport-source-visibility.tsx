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

function pointSourceKey(
  source: PointSourceSchema,
  bounds: ViewportBounds,
  imageToViewport: (x: number, y: number) => Point,
): string | undefined {
  const point = imageToViewport(source.xcentroid, source.ycentroid);
  if (!contains(bounds, point)) {
    return undefined;
  }
  return sourceKey("point", source.source_id);
}

function extendedBox(
  source: ExtendedSourceSchema,
  imageToViewport: (x: number, y: number) => Point,
): ViewportBounds {
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
  return {
    x: Math.min(topLeft.x, bottomRight.x),
    y: Math.min(topLeft.y, bottomRight.y),
    width: Math.abs(bottomRight.x - topLeft.x),
    height: Math.abs(bottomRight.y - topLeft.y),
  };
}

function extendedSourceKey(
  source: ExtendedSourceSchema,
  bounds: ViewportBounds,
  imageToViewport: (x: number, y: number) => Point,
): string | undefined {
  if (!intersects(bounds, extendedBox(source, imageToViewport))) {
    return undefined;
  }
  return sourceKey("extended", source.source_id);
}

export function visibleSourceKeys(
  pointSources: readonly PointSourceSchema[],
  extendedSources: readonly ExtendedSourceSchema[],
  bounds: ViewportBounds,
  imageToViewport: (x: number, y: number) => Point,
): ReadonlySet<string> {
  const keys = [
    ...pointSources.map((source) =>
      pointSourceKey(source, bounds, imageToViewport),
    ),
    ...extendedSources.map((source) =>
      extendedSourceKey(source, bounds, imageToViewport),
    ),
  ];
  return new Set(keys.filter((key): key is string => key !== undefined));
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
    const signature = [...keys]
      .sort((left, right) => left.localeCompare(right))
      .join("|");
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
