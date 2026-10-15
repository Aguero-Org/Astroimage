import type {
  ExtendedSourceSchema,
  GaiaMatchSchema,
} from "@/api/generated/model";
import { MetadataGroup } from "./metadata-group";
import {
  formatSelectionNumber,
  pushGaiaRows,
  type SelectionRow,
} from "./selection-rows";

export function ExtendedSourceDetails({
  source,
  gaiaMatch,
}: Readonly<{ source: ExtendedSourceSchema; gaiaMatch?: GaiaMatchSchema }>) {
  const peak = formatSelectionNumber(source.peak);
  const mean = formatSelectionNumber(source.mean);
  const flux = formatSelectionNumber(source.flux);
  const rows: SelectionRow[] = [
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
  pushGaiaRows(rows, gaiaMatch);

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
