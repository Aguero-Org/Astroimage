import { Download } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { apiBaseUrl } from "@/lib/api-client";

type StoredFitsLinkProps = {
  recordId: string;
  filename: string;
};

export function storedFitsUrl(recordId: string): string {
  return `${apiBaseUrl()}/fits/${recordId}/file`;
}

export function StoredFitsLink({
  recordId,
  filename,
}: Readonly<StoredFitsLinkProps>) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <a
          href={storedFitsUrl(recordId)}
          data-testid="download-stored-fits"
          aria-label={`Descargar ${filename}`}
          className="inline-flex size-8 items-center justify-center rounded-md text-primary hover:bg-accent dark:text-ring"
          onClick={(event) => event.stopPropagation()}
        >
          <Download className="size-4" />
        </a>
      </TooltipTrigger>
      <TooltipContent>Descargar {filename}</TooltipContent>
    </Tooltip>
  );
}
