import { Calendar, CalendarPlus, Filter, Hash, Telescope } from "lucide-react";
import { DateBadge } from "@/components/ui/date-badge";
import { IconValue } from "@/components/ui/icon-value";
import { formatBytes } from "../candidate-api";
import { formatWhen } from "../format-when";
import { CatalogSize } from "./catalog-size";
import { orUnavailable } from "./catalog-value";

export const catalogLabels = {
  displayName: "Nombre de la imagen",
  filename: "Nombre de archivo",
  instrument: "Instrumento",
  proposal: "Número de propuesta",
  filters: "Filtros de la observación",
  observed: "Fecha de observación",
  imported: "Fecha de importación",
  size: "Tamaño del archivo",
} as const;

type CatalogFactsProps = {
  instrument: string | null;
  proposalId: string | null;
  filters: string | null;
  observedAt: string | null;
  importedAt?: string | null;
  sizeBytes: number | null;
};

export function CatalogFacts({
  instrument,
  proposalId,
  filters,
  observedAt,
  importedAt,
  sizeBytes,
}: Readonly<CatalogFactsProps>) {
  return (
    <>
      <IconValue
        label={catalogLabels.instrument}
        value={orUnavailable(instrument)}
        icon={Telescope}
      />
      <IconValue
        label={catalogLabels.proposal}
        value={orUnavailable(proposalId)}
        icon={Hash}
      />
      <IconValue
        label={catalogLabels.filters}
        value={orUnavailable(filters)}
        icon={Filter}
      />
      <DateBadge
        label={catalogLabels.observed}
        value={orUnavailable(formatWhen(observedAt))}
        icon={Calendar}
      />
      {importedAt !== undefined && (
        <DateBadge
          label={catalogLabels.imported}
          value={orUnavailable(formatWhen(importedAt))}
          icon={CalendarPlus}
        />
      )}
      <CatalogSize bytes={sizeBytes} value={formatBytes(sizeBytes)} />
    </>
  );
}
