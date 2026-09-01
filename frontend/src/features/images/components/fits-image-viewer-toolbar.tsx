import { useViewer, useViewerEvent } from "@cellbytes/react-openseadragon";
import { House, Maximize, Minimize, ZoomIn, ZoomOut } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const ZOOM_STEP = 1.2;

export function FitsImageViewerToolbar() {
  const { viewer } = useViewer();
  const [isFullPage, setIsFullPage] = useState(false);
  const disabled = viewer === null;

  useViewerEvent("full-screen", (event) => {
    setIsFullPage(event.fullScreen);
  });

  function zoomIn() {
    viewer?.viewport.zoomBy(ZOOM_STEP);
    viewer?.viewport.applyConstraints();
  }

  function zoomOut() {
    viewer?.viewport.zoomBy(1 / ZOOM_STEP);
    viewer?.viewport.applyConstraints();
  }

  function goHome() {
    viewer?.viewport.goHome();
  }

  function toggleFullPage() {
    viewer?.setFullScreen(!isFullPage);
  }

  return (
    <div className="absolute top-3 right-3 z-10 flex gap-1 rounded-lg border bg-background/90 p-1 shadow-sm backdrop-blur">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={disabled}
        onClick={zoomIn}
        aria-label="Acercar"
      >
        <ZoomIn className="size-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={disabled}
        onClick={zoomOut}
        aria-label="Alejar"
      >
        <ZoomOut className="size-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={disabled}
        onClick={goHome}
        aria-label="Ajustar a la vista"
      >
        <House className="size-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={disabled}
        onClick={toggleFullPage}
        aria-label={
          isFullPage ? "Salir de pantalla completa" : "Pantalla completa"
        }
      >
        {isFullPage ? (
          <Minimize className="size-4" />
        ) : (
          <Maximize className="size-4" />
        )}
      </Button>
    </div>
  );
}
