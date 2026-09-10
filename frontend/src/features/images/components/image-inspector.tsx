import type { CSSProperties, ReactNode } from "react";
import { useState } from "react";
import { HelpHint } from "@/components/ui/help-hint";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { CollapsibleSection } from "./collapsible-section";

type ImageInspectorProps = {
  title?: ReactNode;
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
  title,
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
    <SidebarProvider
      open={isOpen}
      onOpenChange={setOpen}
      defaultOpen={false}
      className="pointer-events-none absolute inset-0 z-30 min-h-0 w-full"
      style={{ "--sidebar-width": "22rem" } as CSSProperties}
    >
      <Sidebar
        id="image-inspector-drawer"
        data-testid="inspector-drawer"
        side="left"
        variant="floating"
        collapsible="offcanvas"
        className="pointer-events-auto top-14"
      >
        <SidebarHeader className="flex-row items-center gap-2 border-b border-sidebar-border px-3 py-3">
          <h2 className="text-sm font-medium">Inspector</h2>
          <HelpHint label="Inspector" testId="help-inspector">
            Controles y metadatos de la imagen. La vista FITS permanece al lado;
            cada sección se abre solo cuando la necesitás.
          </HelpHint>
        </SidebarHeader>
        {workspace}
        <SidebarContent className="gap-0">
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
        </SidebarContent>
      </Sidebar>
      <div className="flex min-w-0 flex-1 flex-col pt-16">
        <div className="flex items-center gap-3 px-4 sm:px-8">
          <SidebarTrigger
            type="button"
            variant="secondary"
            size="icon"
            data-testid="inspector-toggle"
            className="pointer-events-auto size-9 shrink-0 shadow-md"
            aria-controls="image-inspector-drawer"
            aria-label={isOpen ? "Cerrar inspector" : "Abrir inspector"}
          />
          {title}
        </div>
      </div>
    </SidebarProvider>
  );
}
