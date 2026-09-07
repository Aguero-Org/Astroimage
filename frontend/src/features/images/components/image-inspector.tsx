import { Menu, X } from "lucide-react";
import { type ReactNode, useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { cn } from "@/lib/utils";
import { CollapsibleSection } from "./collapsible-section";

type ImageInspectorProps = {
  view: ReactNode;
  sources: ReactNode;
  archive: ReactNode;
  selection: ReactNode;
  selectionOpen?: boolean;
  workspace?: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
};

export function ImageInspector({
  view,
  sources,
  archive,
  selection,
  selectionOpen = false,
  workspace,
  open,
  onOpenChange,
}: Readonly<ImageInspectorProps>) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const isOpen = open ?? uncontrolledOpen;

  function setOpen(next: boolean) {
    onOpenChange?.(next);
    if (open === undefined) {
      setUncontrolledOpen(next);
    }
  }

  return (
    <>
      <Button
        type="button"
        variant="secondary"
        size="icon"
        data-testid="inspector-toggle"
        className="absolute top-16 left-4 z-30 shadow-md sm:left-8"
        aria-expanded={isOpen}
        aria-controls="image-inspector-drawer"
        aria-label={isOpen ? "Cerrar inspector" : "Abrir inspector"}
        onClick={() => setOpen(!isOpen)}
      >
        {isOpen ? <X className="size-4" /> : <Menu className="size-4" />}
      </Button>

      <aside
        id="image-inspector-drawer"
        data-testid="inspector-drawer"
        hidden={!isOpen}
        className={cn(
          "absolute top-28 bottom-4 left-4 z-30 flex w-[min(100%-2rem,22rem)] flex-col overflow-hidden rounded-xl border border-border bg-background/85 shadow-lg backdrop-blur-md sm:bottom-8 sm:left-8",
        )}
      >
        <header className="flex items-center gap-2 border-b border-border px-4 py-3">
          <h2 className="text-sm font-medium">Inspector</h2>
          <HelpHint label="Inspector" testId="help-inspector">
            Controles y metadatos de la imagen. La vista FITS permanece al lado;
            cada sección se abre solo cuando la necesitás.
          </HelpHint>
        </header>
        {workspace}
        <div className="flex-1 overflow-y-auto px-4 py-1">
          <CollapsibleSection id="view" title="Vista">
            {view}
          </CollapsibleSection>
          <CollapsibleSection id="sources" title="Fuentes" defaultOpen>
            {sources}
          </CollapsibleSection>
          <CollapsibleSection
            key={selectionOpen ? "selection-open" : "selection-idle"}
            id="selection"
            title="Selección"
            defaultOpen={selectionOpen}
          >
            {selection}
          </CollapsibleSection>
          <CollapsibleSection id="archive" title="Archivo">
            {archive}
          </CollapsibleSection>
        </div>
      </aside>
    </>
  );
}
