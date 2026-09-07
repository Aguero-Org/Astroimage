import { Menu, X } from "lucide-react";
import { type ReactNode, useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { cn } from "@/lib/utils";
import { CollapsibleSection } from "./collapsible-section";

type ImageInspectorProps = {
  sources: ReactNode;
};

export function ImageInspector({ sources }: Readonly<ImageInspectorProps>) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        type="button"
        variant="secondary"
        size="icon"
        data-testid="inspector-toggle"
        className="absolute top-16 left-4 z-30 shadow-md sm:left-8"
        aria-expanded={open}
        aria-controls="image-inspector-drawer"
        aria-label={open ? "Cerrar inspector" : "Abrir inspector"}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? <X className="size-4" /> : <Menu className="size-4" />}
      </Button>

      <aside
        id="image-inspector-drawer"
        data-testid="inspector-drawer"
        hidden={!open}
        className={cn(
          "absolute top-28 bottom-4 left-4 z-30 flex w-[min(100%-2rem,22rem)] flex-col overflow-hidden rounded-xl border border-white/15 bg-background/85 shadow-lg backdrop-blur-md sm:bottom-8 sm:left-8",
        )}
      >
        <header className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
          <h2 className="text-sm font-medium">Inspector</h2>
          <HelpHint label="Inspector" testId="help-inspector">
            Controles y metadatos de la imagen. La vista FITS permanece al lado;
            cada sección se abre solo cuando la necesitás.
          </HelpHint>
        </header>
        <div className="flex-1 overflow-y-auto px-4 py-1">
          <CollapsibleSection id="view" title="Vista">
            <p className="text-xs text-muted-foreground">
              Stretch, colormap y límites de render se configuran acá.
            </p>
          </CollapsibleSection>
          <CollapsibleSection id="sources" title="Fuentes" defaultOpen>
            {sources}
          </CollapsibleSection>
          <CollapsibleSection id="selection" title="Selección">
            <p className="text-xs text-muted-foreground">
              Al elegir un marcador en la imagen, su información aparece acá.
            </p>
          </CollapsibleSection>
          <CollapsibleSection id="archive" title="Archivo">
            <p className="text-xs text-muted-foreground">
              Metadatos del FITS (instrumento, WCS, HDUs) se agrupan acá.
            </p>
          </CollapsibleSection>
        </div>
      </aside>
    </>
  );
}
