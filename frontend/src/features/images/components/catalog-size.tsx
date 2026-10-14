import { Weight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { orUnavailable } from "./catalog-value";

const MID_BYTES = 50 * 1024 * 1024;
const HEAVY_BYTES = 200 * 1024 * 1024;

type CatalogSizeProps = {
  bytes: number | null;
  value: string;
};

export function CatalogSize({ bytes, value }: Readonly<CatalogSizeProps>) {
  const heavy = bytes !== null && bytes >= HEAVY_BYTES;
  const mid = bytes !== null && bytes >= MID_BYTES && bytes < HEAVY_BYTES;
  const light = bytes !== null && bytes < MID_BYTES;
  let tone: string | undefined;
  if (light) {
    tone = "border-gaia/40 bg-gaia/15 text-gaia";
  } else if (mid) {
    tone =
      "border-amber-500/40 bg-amber-500/15 text-amber-800 dark:text-amber-300";
  } else if (heavy) {
    tone = "border-destructive/40 bg-destructive/15 text-destructive";
  }
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline" className={tone}>
          <Weight aria-hidden />
          <span className="sr-only">Tamaño del archivo</span>
          {orUnavailable(value)}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>Tamaño del archivo</TooltipContent>
    </Tooltip>
  );
}
