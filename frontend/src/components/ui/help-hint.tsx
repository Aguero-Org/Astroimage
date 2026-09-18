import { BookOpen, CircleHelp } from "lucide-react";
import type { ReactNode } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { glossaryPath } from "@/features/glossary/entries";

type HelpHintProps = {
  label: string;
  testId?: string;
  glossaryId?: string;
  children: ReactNode;
};

export function HelpHint({
  label,
  testId,
  glossaryId,
  children,
}: Readonly<HelpHintProps>) {
  return (
    <span className="inline-flex items-center">
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            data-testid={testId}
            className="inline-flex size-6 cursor-help items-center justify-center rounded-full text-muted-foreground hover:text-foreground"
            aria-label={`Ayuda: ${label}`}
          >
            <CircleHelp className="size-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs" side="top">
          {children}
        </TooltipContent>
      </Tooltip>
      {glossaryId ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <a
              href={glossaryPath(glossaryId)}
              data-testid={testId ? `${testId}-glossary` : undefined}
              aria-label={`Ver en el glosario: ${label}`}
              className="inline-flex size-6 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:text-foreground"
            >
              <BookOpen className="size-3.5" />
            </a>
          </TooltipTrigger>
          <TooltipContent side="top">Ver en el glosario</TooltipContent>
        </Tooltip>
      ) : null}
    </span>
  );
}
