import { SquareArrowOutUpRight } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type MastSourceLinkProps = {
  dataUri: string;
};

export function mastFileUrl(dataUri: string): string {
  return `https://mast.stsci.edu/api/v0.1/Download/file?uri=${encodeURIComponent(dataUri)}`;
}

export function MastSourceLink({ dataUri }: Readonly<MastSourceLinkProps>) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <a
          href={mastFileUrl(dataUri)}
          target="_blank"
          rel="noreferrer"
          aria-label={`Archivo original en MAST: ${dataUri}`}
          className="inline-flex size-8 items-center justify-center rounded-md text-primary hover:bg-accent dark:text-ring"
          onClick={(event) => event.stopPropagation()}
        >
          <SquareArrowOutUpRight className="size-4" />
        </a>
      </TooltipTrigger>
      <TooltipContent>{dataUri}</TooltipContent>
    </Tooltip>
  );
}
