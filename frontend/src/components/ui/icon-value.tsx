import type { LucideIcon } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type IconValueProps = {
  label: string;
  value: string;
  icon: LucideIcon;
};

export function IconValue({
  label,
  value,
  icon: Icon,
}: Readonly<IconValueProps>) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex min-w-0 items-center gap-1 text-sm">
          <Icon
            className="size-3.5 shrink-0 text-muted-foreground"
            aria-hidden
          />
          <span className="sr-only">{label}</span>
          <span className="truncate">{value}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
