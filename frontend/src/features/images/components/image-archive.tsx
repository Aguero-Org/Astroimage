import type { FitsMetadataSchema } from "@/api/generated/model";
import { Skeleton } from "@/components/ui/skeleton";
import { CollapsibleSection } from "./collapsible-section";
import { MetadataGroup, type MetadataRow } from "./metadata-group";

type ImageArchiveProps = {
  info: FitsMetadataSchema | undefined;
  isPending: boolean;
};

function formatNumber(
  value: number | null | undefined,
  digits = 4,
): string | null {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }
  return value.toPrecision(digits);
}

function formatList(
  values: Array<string | number> | null | undefined,
): string | null {
  if (!values || values.length === 0) {
    return null;
  }
  return values.join(" × ");
}

function row(
  id: string,
  label: string,
  value: string | number | null | undefined,
  help: string,
): MetadataRow | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  return { id, label, value: String(value), help };
}

export function ImageArchive({ info, isPending }: Readonly<ImageArchiveProps>) {
  if (isPending) {
    return <Skeleton className="h-24 w-full rounded-md" />;
  }
  if (!info) {
    return (
      <p className="text-xs text-muted-foreground">
        No hay metadatos disponibles.
      </p>
    );
  }

  const instrumentRows = [
    row(
      "telescope",
      "Telescopio",
      info.instrument?.telescope,
      "Observatorio o misión que tomó la exposición.",
    ),
    row(
      "instrument",
      "Instrumento",
      info.instrument?.instrument,
      "Cámara o espectrógrafo montado en el telescopio.",
    ),
    row(
      "detector",
      "Detector",
      info.instrument?.detector,
      "Chip o canal del instrumento.",
    ),
    row(
      "filter",
      "Filtro",
      info.instrument?.filter_name,
      "Banda fotométrica de la exposición.",
    ),
    row(
      "exptime",
      "Exposición",
      formatNumber(info.instrument?.exptime, 5),
      "Tiempo de integración, en segundos.",
    ),
    row(
      "date-obs",
      "Fecha",
      info.instrument?.date_obs,
      "Fecha de observación (DATE-OBS).",
    ),
    row(
      "time-obs",
      "Hora",
      info.instrument?.time_obs,
      "Hora de observación (TIME-OBS).",
    ),
  ].filter((item) => item !== null);

  const imageRows = [
    row(
      "shape",
      "Tamaño",
      formatList(info.image?.shape),
      "Dimensiones del arreglo de píxeles (filas × columnas).",
    ),
    row(
      "unit",
      "Unidad",
      info.image?.unit,
      "Unidad física de los valores de píxel.",
    ),
    row(
      "datamin",
      "Mínimo",
      formatNumber(info.image?.datamin),
      "Valor mínimo en el HDU de imagen.",
    ),
    row(
      "datamax",
      "Máximo",
      formatNumber(info.image?.datamax),
      "Valor máximo en el HDU de imagen.",
    ),
    row(
      "datamean",
      "Media",
      formatNumber(info.image?.datamean),
      "Promedio de los píxeles.",
    ),
    row(
      "median",
      "Mediana",
      formatNumber(info.image?.median),
      "Mediana de los píxeles.",
    ),
    row(
      "background",
      "Fondo",
      formatNumber(info.image?.background),
      "Estimación del cielo o fondo.",
    ),
  ].filter((item) => item !== null);

  const photoRows = [
    row(
      "photflam",
      "PHOTFLAM",
      formatNumber(info.photometry?.photflam),
      "Factor de conversión de cuentas a flujo.",
    ),
    row(
      "photplam",
      "PHOTPLAM",
      formatNumber(info.photometry?.photplam),
      "Longitud de onda pivot, en ångströms.",
    ),
    row(
      "photbw",
      "PHOTBW",
      formatNumber(info.photometry?.photbw),
      "Ancho de banda equivalente del filtro.",
    ),
  ].filter((item) => item !== null);

  const wcsPresent = info.wcs?.present ? "Sí" : info.wcs ? "No" : null;
  const wcsRows = [
    row(
      "wcs-present",
      "WCS",
      wcsPresent,
      "Si el HDU trae una solución astrométrica (coordenadas en el cielo).",
    ),
    row("wcs-naxis", "NAXIS", info.wcs?.naxis, "Cantidad de ejes del WCS."),
    row(
      "wcs-ctype",
      "CTYPE",
      info.wcs?.ctype?.join(", "),
      "Tipos de coordenadas (p. ej. RA---TAN, DEC--TAN).",
    ),
    row(
      "wcs-crval",
      "CRVAL",
      info.wcs?.crval?.map((value) => value.toPrecision(6)).join(", "),
      "Coordenadas del píxel de referencia.",
    ),
    row(
      "wcs-crpix",
      "CRPIX",
      info.wcs?.crpix?.map((value) => value.toPrecision(6)).join(", "),
      "Píxel de referencia en el detector.",
    ),
  ].filter((item) => item !== null);

  const hduRows =
    info.hdus.images
      ?.map((hdu) =>
        row(
          `hdu-${hdu.index}`,
          `HDU ${hdu.index}`,
          [hdu.extname, hdu.kind, formatList(hdu.shape)]
            .filter(Boolean)
            .join(" · ") || String(hdu.index),
          "Extensión de imagen 2D disponible en el FITS.",
        ),
      )
      .filter((item) => item !== null) ?? [];

  const tableRows =
    info.tables
      ?.map((table) =>
        row(
          `table-${table.index}`,
          table.name || `Tabla ${table.index}`,
          `${table.rows} filas · ${table.columns.length} columnas`,
          "Tabla binaria embebida en el FITS (catálogo o calibración).",
        ),
      )
      .filter((item) => item !== null) ?? [];

  const headerEntries = Object.entries(info.header ?? {});

  return (
    <div data-testid="image-archive">
      <MetadataGroup
        title="Instrumento"
        testId="archive-instrument"
        rows={instrumentRows}
      />
      <MetadataGroup title="Imagen" testId="archive-image" rows={imageRows} />
      <MetadataGroup
        title="Fotometría"
        testId="archive-photometry"
        rows={photoRows}
      />
      <MetadataGroup title="WCS" testId="archive-wcs" rows={wcsRows} />
      <MetadataGroup title="HDUs" testId="archive-hdus" rows={hduRows} />
      <MetadataGroup title="Tablas" testId="archive-tables" rows={tableRows} />
      {headerEntries.length > 0 ? (
        <CollapsibleSection id="archive-header" title="Header FITS">
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
            {headerEntries.map(([key, headerValue]) => (
              <div key={key} className="contents">
                <dt className="text-muted-foreground">{key}</dt>
                <dd className="truncate">{String(headerValue)}</dd>
              </div>
            ))}
          </dl>
        </CollapsibleSection>
      ) : null}
    </div>
  );
}
