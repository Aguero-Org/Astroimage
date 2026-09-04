import {
  TiledImage,
  useOpenseadragon,
  ViewerStateProvider,
} from "@cellbytes/react-openseadragon";
import { useId, useMemo } from "react";
import type { PointSourceSchema } from "@/api/generated/model";
import { cn } from "@/lib/utils";
import { FITS_RENDER_IMAGE_KEY } from "../source-detection";
import { FitsImageViewerToolbar } from "./fits-image-viewer-toolbar";
import { SourceMarkers } from "./source-markers";

type FitsImageViewerProps = {
  imageUrl: string;
  label: string;
  className?: string;
  pointSources?: PointSourceSchema[];
};

export function FitsImageViewer({
  imageUrl,
  label,
  className,
  pointSources = [],
}: Readonly<FitsImageViewerProps>) {
  const viewerId = useId().replaceAll(":", "");
  const navigatorId = `fits-osd-nav-${viewerId}`;
  const options = useMemo(
    () => ({
      id: `fits-osd-${viewerId}`,
      showNavigationControl: false,
      showNavigator: true,
      navigatorId,
      navigatorBackground: "transparent",
      navigatorAutoFade: false,
      animationTime: 0.4,
      minZoomImageRatio: 0.8,
      maxZoomPixelRatio: 8,
      visibilityRatio: 0.5,
      constrainDuringPan: true,
      gestureSettingsMouse: {
        clickToZoom: true,
        dblClickToZoom: true,
        flickEnabled: true,
      },
    }),
    [navigatorId, viewerId],
  );
  const state = useOpenseadragon({ options });
  const tileSource = useMemo(
    () => ({
      type: "image",
      url: imageUrl,
      buildPyramid: true,
    }),
    [imageUrl],
  );

  return (
    <ViewerStateProvider state={state}>
      <div
        className={cn(
          "relative overflow-hidden rounded-xl border bg-transparent",
          className,
        )}
      >
        <div
          ref={state.setContainerElement}
          role="application"
          aria-label={label}
          className="fits-osd h-[min(70vh,40rem)] w-full bg-transparent"
        />
        <div
          id={navigatorId}
          className="pointer-events-auto absolute right-3 bottom-3 h-28 w-40 overflow-hidden rounded-md border bg-transparent shadow-sm"
        />
        <SourceMarkers sources={pointSources} />
        <FitsImageViewerToolbar />
      </div>
      <TiledImage imageKey={FITS_RENDER_IMAGE_KEY} tileSource={tileSource} />
    </ViewerStateProvider>
  );
}
