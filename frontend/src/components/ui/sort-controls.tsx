import {
  ArrowDownNarrowWide,
  ArrowUpNarrowWide,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type SortField<Field extends string> = {
  field: Field;
  label: string;
  icon: LucideIcon;
};

type SortControlsProps<Field extends string> = {
  fields: readonly SortField<Field>[];
  sort: Field;
  order: "asc" | "desc";
  onSort: (field: Field) => void;
};

export function SortControls<Field extends string>({
  fields,
  sort,
  order,
  onSort,
}: Readonly<SortControlsProps<Field>>) {
  const descending = order === "desc";

  return (
    <div className="flex items-center gap-2">
      <Select
        value={sort}
        onValueChange={(value) => {
          const next = fields.find((field) => field.field === value);
          if (next !== undefined) {
            onSort(next.field);
          }
        }}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-flex">
              <SelectTrigger
                className="h-9 w-auto gap-1.5 px-2.5"
                aria-label="Criterio de ordenación"
              >
                <SelectValue />
              </SelectTrigger>
            </span>
          </TooltipTrigger>
          <TooltipContent>Criterio de ordenación</TooltipContent>
        </Tooltip>
        <SelectContent>
          {fields.map((field) => {
            const Icon = field.icon;
            return (
              <SelectItem key={field.field} value={field.field}>
                <span className="inline-flex items-center gap-2">
                  <Icon className="size-4" />
                  {field.label}
                </span>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label={descending ? "Orden descendente" : "Orden ascendente"}
            onClick={() => onSort(sort)}
          >
            {descending ? <ArrowDownNarrowWide /> : <ArrowUpNarrowWide />}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {descending ? "Orden descendente" : "Orden ascendente"}
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
