import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type DateBadgeProps = {
  label: string;
  value: string;
  icon: LucideIcon;
};

export function DateBadge({
  label,
  value,
  icon: Icon,
}: Readonly<DateBadgeProps>) {
  const shown = value.split(",")[0] ?? value;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline">
          <Icon aria-hidden />
          <span className="sr-only">{label}</span>
          {shown}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
