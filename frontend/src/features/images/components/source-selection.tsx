import type { PointSourceSchema } from "@/api/generated/model";
import { MetadataGroup } from "./metadata-group";

type SourceSelectionProps = {
  source: PointSourceSchema | null;
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

  const rows = [
    {
      id: "sel-rank",
      label: "Rank",
      value: String(source.rank),
      help: "Orden de relevancia entre las fuentes detectadas (1 es la más relevante).",
    },
    {
      id: "sel-snr",
      label: "SNR",
      value: source.snr.toFixed(2),
      help: "Relación señal/ruido del pico.",
    },
    {
      id: "sel-score",
      label: "Score",
      value: source.relevance_score.toFixed(3),
      help: "Puntuación de relevancia combinada (0 a 1).",
    },
    {
      id: "sel-x",
      label: "X",
      value: source.xcentroid.toFixed(2),
      help: "Centroide en píxeles, eje X.",
    },
    {
      id: "sel-y",
      label: "Y",
      value: source.ycentroid.toFixed(2),
      help: "Centroide en píxeles, eje Y.",
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
    });
  }
  if (flux) {
    rows.push({
      id: "sel-flux",
      label: "Flux",
      value: flux,
      help: "Flujo estimado de la fuente puntual.",
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
