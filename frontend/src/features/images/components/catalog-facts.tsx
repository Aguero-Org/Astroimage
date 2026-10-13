import { Calendar, CalendarPlus, Filter, Hash, Telescope } from "lucide-react";
import { formatBytes } from "../candidate-api";
import { formatWhen } from "../format-when";
import { CatalogDate, CatalogIconValue, CatalogSize } from "./catalog-card";

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
      <CatalogIconValue
        label={catalogLabels.instrument}
        value={instrument}
        icon={Telescope}
      />
      <CatalogIconValue
        label={catalogLabels.proposal}
        value={proposalId}
        icon={Hash}
      />
      <CatalogIconValue
        label={catalogLabels.filters}
        value={filters}
        icon={Filter}
      />
      <CatalogDate
        label={catalogLabels.observed}
        value={formatWhen(observedAt)}
        icon={Calendar}
      />
      {importedAt !== undefined && (
        <CatalogDate
          label={catalogLabels.imported}
          value={formatWhen(importedAt)}
          icon={CalendarPlus}
        />
      )}
      <CatalogSize bytes={sizeBytes} value={formatBytes(sizeBytes)} />
    </>
  );
}
