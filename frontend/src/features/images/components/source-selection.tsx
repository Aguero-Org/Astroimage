import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { MetadataGroup } from "./metadata-group";

export type SelectedSource = PointSourceSchema | ExtendedSourceSchema;

type SourceSelectionProps = {
  source: SelectedSource | null;
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

export function SourceSelection({ source }: Readonly<SourceSelectionProps>) {
  if (!source) {
    return (
      <p className="text-xs text-muted-foreground">
        Elegí un marcador en la imagen para ver sus datos.
      </p>
    );
  }

  if (source.object_type === "extended") {
    return <ExtendedSourceDetails source={source} />;
  }

  const rows = [
    {
      id: "sel-rank",
      label: "Rank",
      value: String(source.rank),
      help: "Orden de relevancia entre las fuentes detectadas (1 es la más relevante).",
      glossaryId: "rank",
    },
    ...("snr" in source
      ? [
          {
            id: "sel-snr",
            label: "SNR",
            value: source.snr.toFixed(2),
            help: "Relación señal/ruido del pico.",
            glossaryId: "snr",
          },
        ]
      : []),
    {
      id: "sel-score",
      label: "Score",
      value: source.relevance_score.toFixed(3),
      help: "Puntuación de relevancia combinada (0 a 1).",
      glossaryId: "score",
    },
    {
      id: "sel-x",
      label: "X",
      value: source.xcentroid.toFixed(2),
      help: "Centroide en píxeles, eje X.",
      glossaryId: "centroide",
    },
    {
      id: "sel-y",
      label: "Y",
      value: source.ycentroid.toFixed(2),
      help: "Centroide en píxeles, eje Y.",
      glossaryId: "centroide",
    },
  ];
  const peak = formatNumber(source.peak);
  const flux = formatNumber(source.flux);
  if (peak) {
    rows.push({
      id: "sel-peak",
      label: "Peak",
      value: peak,
      help: "Valor de píxel en el máximo del pico.",
      glossaryId: "peak",
    });
  }
  if (flux) {
    rows.push({
      id: "sel-flux",
      label: "Flux",
      value: flux,
      help: "Flujo estimado de la fuente puntual.",
      glossaryId: "flux",
    });
  }

  return (
    <div data-testid="source-selection">
      <MetadataGroup
        title={`Fuente ${source.source_id}`}
        testId="archive-selection"
        rows={rows}
      />
    </div>
  );
}

function ExtendedSourceDetails({
  source,
}: Readonly<{ source: ExtendedSourceSchema }>) {
  const peak = formatNumber(source.peak);
  const mean = formatNumber(source.mean);
  const flux = formatNumber(source.flux);
  const rows = [
    {
      id: "sel-rank",
      label: "Rank",
      value: String(source.rank),
      help: "Orden de relevancia entre las estructuras detectadas (1 es la más relevante).",
      glossaryId: "rank",
    },
    {
      id: "sel-score",
      label: "Score",
      value: source.relevance_score.toFixed(3),
      help: "Puntuación de relevancia combinada (0 a 1).",
      glossaryId: "score",
    },
    {
      id: "sel-x",
      label: "X",
      value: source.xcentroid.toFixed(2),
      help: "Centroide de la región en píxeles, eje X.",
      glossaryId: "centroide",
    },
    {
      id: "sel-y",
      label: "Y",
      value: source.ycentroid.toFixed(2),
      help: "Centroide de la región en píxeles, eje Y.",
      glossaryId: "centroide",
    },
    {
      id: "sel-width",
      label: "Ancho",
      value: `${source.width_pixels.toFixed(1)} px`,
      help: "Extensión horizontal del recuadro que envuelve la región.",
      glossaryId: "ancho-alto",
    },
    {
      id: "sel-height",
      label: "Alto",
      value: `${source.height_pixels.toFixed(1)} px`,
      help: "Extensión vertical del recuadro que envuelve la región.",
      glossaryId: "ancho-alto",
    },
    {
      id: "sel-area",
      label: "Área",
      value: `${source.area_pixels} px²`,
      help: "Cantidad de píxeles que ocupa la región detectada.",
      glossaryId: "area",
    },
  ];
  if (peak) {
    rows.push({
      id: "sel-peak",
      label: "Peak",
      value: peak,
      help: "Valor de píxel en el máximo de la región.",
      glossaryId: "peak",
    });
  }
  if (mean) {
    rows.push({
      id: "sel-mean",
      label: "Media",
      value: mean,
      help: "Valor medio de píxel dentro de la región.",
      glossaryId: "mean",
    });
  }
  if (flux) {
    rows.push({
      id: "sel-flux",
      label: "Flux",
      value: flux,
      help: "Flujo estimado de la estructura extendida.",
      glossaryId: "flux",
    });
  }

  return (
    <div data-testid="extended-source-selection">
      <MetadataGroup
        title={`Fuente extendida ${source.source_id}`}
        testId="archive-extended-selection"
        rows={rows}
      />
    </div>
  );
}
