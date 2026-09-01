import {
  TiledImage,
  useOpenseadragon,
  ViewerStateProvider,
} from "@cellbytes/react-openseadragon";
import { useId, useMemo } from "react";
import { cn } from "@/lib/utils";
import { FitsImageViewerToolbar } from "./fits-image-viewer-toolbar";

type FitsImageViewerProps = {
  imageUrl: string;
  label: string;
  className?: string;
};

export function FitsImageViewer({
  imageUrl,
  label,
  className,
}: FitsImageViewerProps) {
  const viewerId = useId().replaceAll(":", "");
  const navigatorId = `fits-osd-nav-${viewerId}`;
  const options = useMemo(
    () => ({
      id: `fits-osd-${viewerId}`,
      showNavigationControl: false,
      showNavigator: true,
      navigatorId,
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
          "relative overflow-hidden rounded-xl border bg-card",
          className,
        )}
      >
        <div
          ref={state.setContainerElement}
          role="img"
          aria-label={label}
          className="h-[min(70vh,40rem)] w-full bg-black"
        />
        <div
          id={navigatorId}
          className="pointer-events-auto absolute right-3 bottom-3 h-28 w-40 overflow-hidden rounded-md border bg-card shadow-sm"
        />
        <FitsImageViewerToolbar />
      </div>
      <TiledImage imageKey="fits-render" tileSource={tileSource} />
    </ViewerStateProvider>
  );
}
