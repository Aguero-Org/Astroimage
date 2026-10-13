import {
  ArrowDownNarrowWide,
  ArrowUpNarrowWide,
  type LucideIcon,
  Weight,
} from "lucide-react";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

type CatalogListProps = {
  children: ReactNode;
  testId?: string;
};

export function CatalogList({ children, testId }: Readonly<CatalogListProps>) {
  return (
    <ul data-testid={testId} className="flex w-full flex-col gap-3">
      {children}
    </ul>
  );
}

type CatalogCardProps = {
  title: ReactNode;
  detail?: ReactNode;
  meta: ReactNode;
  actions: ReactNode;
  testId?: string;
};

export function CatalogCard({
  title,
  detail,
  meta,
  actions,
  testId,
}: Readonly<CatalogCardProps>) {
  return (
    <li>
      <Card className="gap-2 py-3" data-testid={testId}>
        <CardHeader className="px-4">
          <CardTitle className="text-base">{title}</CardTitle>
          {detail !== undefined && <CardDescription>{detail}</CardDescription>}
          <CardAction className="flex items-center gap-1">{actions}</CardAction>
        </CardHeader>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4">
          {meta}
        </div>
      </Card>
    </li>
  );
}

export function orUnavailable(value: string | null | undefined): string {
  if (
    value === null ||
    value === undefined ||
    value.trim() === "" ||
    value === "—" ||
    value === "--" ||
    value === "-"
  ) {
    return "No disponible";
  }
  return value;
}

type CatalogIconValueProps = {
  label: string;
  value: string | null;
  icon: LucideIcon;
};

export function CatalogIconValue({
  label,
  value,
  icon: Icon,
}: Readonly<CatalogIconValueProps>) {
  const shown = orUnavailable(value);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex min-w-0 items-center gap-1 text-sm">
          <Icon
            className="size-3.5 shrink-0 text-muted-foreground"
            aria-hidden
          />
          <span className="sr-only">{label}</span>
          <span className="truncate">{shown}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

type CatalogMarkProps = {
  label: string;
  value: string;
  icon: LucideIcon;
};

export function CatalogDate({
  label,
  value,
  icon: Icon,
}: Readonly<CatalogMarkProps>) {
  const available = orUnavailable(value);
  const shown =
    available === "No disponible"
      ? available
      : (available.split(",")[0] ?? available);
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

const MID_BYTES = 50 * 1024 * 1024;
const HEAVY_BYTES = 200 * 1024 * 1024;

export function CatalogSize({
  bytes,
  value,
}: Readonly<{ bytes: number | null; value: string }>) {
  const heavy = bytes !== null && bytes >= HEAVY_BYTES;
  const mid = bytes !== null && bytes >= MID_BYTES && bytes < HEAVY_BYTES;
  const light = bytes !== null && bytes < MID_BYTES;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          variant="outline"
          className={
            light
              ? "border-gaia/40 bg-gaia/15 text-gaia"
              : mid
                ? "border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-300"
                : heavy
                  ? "border-destructive/40 bg-destructive/15 text-destructive"
                  : undefined
          }
        >
          <Weight aria-hidden />
          <span className="sr-only">Tamaño del archivo</span>
          {orUnavailable(value)}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>Tamaño del archivo</TooltipContent>
    </Tooltip>
  );
}

export type CatalogSortField<Field extends string> = {
  field: Field;
  label: string;
  icon: LucideIcon;
};

type CatalogSortProps<Field extends string> = {
  fields: readonly CatalogSortField<Field>[];
  sort: Field;
  order: "asc" | "desc";
  onSort: (field: Field) => void;
};

export function CatalogSort<Field extends string>({
  fields,
  sort,
  order,
  onSort,
}: Readonly<CatalogSortProps<Field>>) {
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
