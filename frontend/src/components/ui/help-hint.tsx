import { CircleHelp } from "lucide-react";
import type { ReactNode } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type HelpHintProps = {
  label: string;
  testId?: string;
  children: ReactNode;
};

export function HelpHint({ label, testId, children }: Readonly<HelpHintProps>) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          data-testid={testId}
          className="inline-flex size-4 cursor-help items-center justify-center rounded-full text-muted-foreground hover:text-foreground"
          aria-label={`Ayuda: ${label}`}
        >
          <CircleHelp className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs" side="top">
        {children}
      </TooltipContent>
    </Tooltip>
  );
}
