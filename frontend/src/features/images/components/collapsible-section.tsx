import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
} from "@/components/ui/sidebar";

type CollapsibleSectionProps = {
  id: string;
  title: string;
  hint?: ReactNode;
  defaultOpen?: boolean;
  nested?: boolean;
  children: ReactNode;
};

export function CollapsibleSection({
  id,
  title,
  hint,
  defaultOpen = false,
  nested = false,
  children,
}: Readonly<CollapsibleSectionProps>) {
  return (
    <Collapsible
      defaultOpen={defaultOpen}
      className="group/collapsible"
      data-testid={`inspector-section-${id}`}
    >
      <SidebarGroup className="px-2 py-0">
        <div
          className={`sticky z-30 flex h-8 w-full items-center bg-sidebar ${nested ? "top-8" : "top-0"}`}
        >
          <SidebarGroupLabel
            asChild
            className="h-8 min-w-0 flex-1 bg-transparent px-0 py-0 text-sm text-sidebar-foreground"
          >
            <CollapsibleTrigger
              type="button"
              data-testid={`inspector-section-${id}-toggle`}
              className="flex h-8 w-full cursor-pointer items-center justify-between gap-2 py-0"
            >
              {title}
              <ChevronDown className="size-4 shrink-0 transition-transform group-data-[state=closed]/collapsible:-rotate-90" />
            </CollapsibleTrigger>
          </SidebarGroupLabel>
          {hint}
        </div>
        <CollapsibleContent>
          <SidebarGroupContent className="pb-1">{children}</SidebarGroupContent>
        </CollapsibleContent>
      </SidebarGroup>
    </Collapsible>
  );
}
