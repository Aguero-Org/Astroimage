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
  defaultOpen?: boolean;
  children: ReactNode;
};

export function CollapsibleSection({
  id,
  title,
  defaultOpen = false,
  children,
}: Readonly<CollapsibleSectionProps>) {
  return (
    <Collapsible
      defaultOpen={defaultOpen}
      className="group/collapsible"
      data-testid={`inspector-section-${id}`}
    >
      <SidebarGroup>
        <SidebarGroupLabel
          asChild
          className="h-auto w-full text-sm text-sidebar-foreground"
        >
          <CollapsibleTrigger
            type="button"
            data-testid={`inspector-section-${id}-toggle`}
            className="flex w-full cursor-pointer items-center justify-between gap-2 py-1"
          >
            {title}
            <ChevronDown className="size-4 shrink-0 transition-transform group-data-[state=closed]/collapsible:-rotate-90" />
          </CollapsibleTrigger>
        </SidebarGroupLabel>
        <CollapsibleContent>
          <SidebarGroupContent className="pt-2 pb-1">
            {children}
          </SidebarGroupContent>
        </CollapsibleContent>
      </SidebarGroup>
    </Collapsible>
  );
}
