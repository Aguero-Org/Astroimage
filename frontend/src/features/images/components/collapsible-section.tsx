import { ChevronDown } from "lucide-react";
import { type ReactNode, useState } from "react";
import { cn } from "@/lib/utils";

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
  const [open, setOpen] = useState(defaultOpen);
  const panelId = `${id}-panel`;

  return (
    <section
      data-testid={`inspector-section-${id}`}
      className="border-b border-white/10 py-2 last:border-b-0"
    >
      <button
        type="button"
        data-testid={`inspector-section-${id}-toggle`}
        className="flex w-full cursor-pointer items-center justify-between gap-2 py-1 text-left text-sm font-medium"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        {title}
        <ChevronDown
          className={cn(
            "size-4 shrink-0 transition-transform",
            open ? "rotate-0" : "-rotate-90",
          )}
        />
      </button>
      <div id={panelId} hidden={!open} className="pt-2 pb-1">
        {children}
      </div>
    </section>
  );
}
