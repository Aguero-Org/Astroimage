import { Link } from "@tanstack/react-router";
import { CircleHelp, ExternalLink } from "lucide-react";
import type { ReactNode } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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
        <span className="inline-flex items-start gap-2">
          <span>{children}</span>
          {glossaryId ? (
            <Link
              to="/glossary"
              hash={glossaryId}
              data-testid={testId ? `${testId}-glossary` : undefined}
              aria-label={`Abrir glosario: ${label}`}
              className="inline-flex size-6 shrink-0 items-center justify-center rounded-full text-background hover:opacity-80"
            >
              <ExternalLink className="size-3.5" />
            </Link>
          ) : null}
        </span>
      </TooltipContent>
    </Tooltip>
  );
}
