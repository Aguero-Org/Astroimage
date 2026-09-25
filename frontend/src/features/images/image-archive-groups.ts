import type { FitsMetadataSchema } from "@/api/generated/model";
import type { MetadataRow } from "./components/metadata-group";

export type ArchiveField = {
  id: string;
  label: string;
  help: string;
  glossaryId?: string;
  read: (info: FitsMetadataSchema) => string | null;
};

export type ArchiveGroup = {
  title: string;
  testId: string;
  fields?: readonly ArchiveField[];
  rows?: (info: FitsMetadataSchema) => MetadataRow[];
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

function fieldRow(
  field: ArchiveField,
  info: FitsMetadataSchema,
): MetadataRow | null {
  const value = field.read(info);
  if (value === null || value === "") {
    return null;
  }
  return {
    id: field.id,
    label: field.label,
    value,
    help: field.help,
    glossaryId: field.glossaryId,
  };
}

export function archiveGroupRows(
  group: ArchiveGroup,
  info: FitsMetadataSchema,
): MetadataRow[] {
  if (group.rows) {
    return group.rows(info);
  }
  return (group.fields ?? []).flatMap((field) => {
    const next = fieldRow(field, info);
    return next ? [next] : [];
  });
}

export const IMAGE_ARCHIVE_GROUPS: readonly ArchiveGroup[] = [
  {
    title: "Instrumento",
    testId: "archive-instrument",
    fields: [
      {
        id: "telescope",
        label: "Telescopio",
        help: "Observatorio o misión que tomó la exposición.",
        glossaryId: "instrumento",
        read: (info) => info.instrument?.telescope ?? null,
      },
      {
        id: "instrument",
        label: "Instrumento",
        help: "Cámara o espectrógrafo montado en el telescopio.",
        glossaryId: "instrumento",
        read: (info) => info.instrument?.instrument ?? null,
      },
      {
        id: "detector",
        label: "Detector",
        help: "Chip o canal del instrumento.",
        glossaryId: "instrumento",
        read: (info) => info.instrument?.detector ?? null,
      },
      {
        id: "filter",
        label: "Filtro",
        help: "Banda fotométrica de la exposición.",
        glossaryId: "instrumento",
        read: (info) => info.instrument?.filter_name ?? null,
      },
      {
        id: "exptime",
        label: "Exposición",
        help: "Tiempo de integración, en segundos.",
        glossaryId: "instrumento",
        read: (info) => formatNumber(info.instrument?.exptime, 5),
      },
      {
        id: "date-obs",
        label: "Fecha",
        help: "Fecha de observación (DATE-OBS).",
        glossaryId: "instrumento",
        read: (info) => info.instrument?.date_obs ?? null,
      },
      {
        id: "time-obs",
        label: "Hora",
        help: "Hora de observación (TIME-OBS).",
        glossaryId: "instrumento",
        read: (info) => info.instrument?.time_obs ?? null,
      },
    ],
  },
  {
    title: "Imagen",
    testId: "archive-image",
    fields: [
      {
        id: "shape",
        label: "Tamaño",
        help: "Dimensiones del arreglo de píxeles (filas × columnas).",
        glossaryId: "imagen-pixeles",
        read: (info) => formatList(info.image?.shape),
      },
      {
        id: "unit",
        label: "Unidad",
        help: "Unidad física de los valores de píxel.",
        glossaryId: "imagen-pixeles",
        read: (info) => info.image?.unit ?? null,
      },
      {
        id: "datamin",
        label: "Mínimo",
        help: "Valor mínimo en el HDU de imagen.",
        glossaryId: "imagen-pixeles",
        read: (info) => formatNumber(info.image?.datamin),
      },
      {
        id: "datamax",
        label: "Máximo",
        help: "Valor máximo en el HDU de imagen.",
        glossaryId: "imagen-pixeles",
        read: (info) => formatNumber(info.image?.datamax),
      },
      {
        id: "datamean",
        label: "Media",
        help: "Promedio de los píxeles.",
        glossaryId: "imagen-pixeles",
        read: (info) => formatNumber(info.image?.datamean),
      },
      {
        id: "median",
        label: "Mediana",
        help: "Mediana de los píxeles.",
        glossaryId: "imagen-pixeles",
        read: (info) => formatNumber(info.image?.median),
      },
      {
        id: "background",
        label: "Fondo",
        help: "Estimación del cielo o fondo.",
        glossaryId: "imagen-pixeles",
        read: (info) => formatNumber(info.image?.background),
      },
    ],
  },
  {
    title: "Fotometría",
    testId: "archive-photometry",
    fields: [
      {
        id: "photflam",
        label: "PHOTFLAM",
        help: "Factor de conversión de cuentas a flujo.",
        glossaryId: "fotometria",
        read: (info) => formatNumber(info.photometry?.photflam),
      },
      {
        id: "photplam",
        label: "PHOTPLAM",
        help: "Longitud de onda pivot, en ångströms.",
        glossaryId: "fotometria",
        read: (info) => formatNumber(info.photometry?.photplam),
      },
      {
        id: "photbw",
        label: "PHOTBW",
        help: "Ancho de banda equivalente del filtro.",
        glossaryId: "fotometria",
        read: (info) => formatNumber(info.photometry?.photbw),
      },
    ],
  },
  {
    title: "WCS",
    testId: "archive-wcs",
    fields: [
      {
        id: "wcs-present",
        label: "WCS",
        help: "Si el HDU trae una solución astrométrica (coordenadas en el cielo).",
        glossaryId: "wcs",
        read: (info) => {
          if (!info.wcs) {
            return null;
          }
          return info.wcs.present ? "Sí" : "No";
        },
      },
      {
        id: "wcs-naxis",
        label: "NAXIS",
        help: "Cantidad de ejes del WCS.",
        glossaryId: "wcs",
        read: (info) =>
          info.wcs?.naxis === undefined ? null : String(info.wcs.naxis),
      },
      {
        id: "wcs-ctype",
        label: "CTYPE",
        help: "Tipos de coordenadas (p. ej. RA---TAN, DEC--TAN).",
        glossaryId: "wcs",
        read: (info) => info.wcs?.ctype?.join(", ") ?? null,
      },
      {
        id: "wcs-crval",
        label: "CRVAL",
        help: "Coordenadas del píxel de referencia.",
        glossaryId: "wcs",
        read: (info) =>
          info.wcs?.crval?.map((value) => value.toPrecision(6)).join(", ") ??
          null,
      },
      {
        id: "wcs-crpix",
        label: "CRPIX",
        help: "Píxel de referencia en el detector.",
        glossaryId: "wcs",
        read: (info) =>
          info.wcs?.crpix?.map((value) => value.toPrecision(6)).join(", ") ??
          null,
      },
    ],
  },
  {
    title: "HDUs",
    testId: "archive-hdus",
    rows: (info) =>
      (info.hdus.images ?? []).flatMap((hdu) => {
        const value =
          [hdu.extname, hdu.kind, formatList(hdu.shape)]
            .filter(Boolean)
            .join(" · ") || String(hdu.index);
        return [
          {
            id: `hdu-${hdu.index}`,
            label: `HDU ${hdu.index}`,
            value,
            help: "Extensión de imagen 2D disponible en el FITS.",
            glossaryId: "hdu",
          },
        ];
      }),
  },
  {
    title: "Tablas",
    testId: "archive-tables",
    rows: (info) =>
      (info.tables ?? []).map((table) => ({
        id: `table-${table.index}`,
        label: table.name || `Tabla ${table.index}`,
        value: `${table.rows} filas · ${table.columns.length} columnas`,
        help: "Tabla binaria embebida en el FITS (catálogo o calibración).",
        glossaryId: "tabla-fits",
      })),
  },
];
