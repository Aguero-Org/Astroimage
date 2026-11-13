import type { GaiaMatchSchema } from "@/api/generated/model";

export type SelectionRow = {
  id: string;
  label: string;
  value: string;
  help: string;
  glossaryId: string;
};

export function pushGaiaRows(
  rows: SelectionRow[],
  gaiaMatch: GaiaMatchSchema | undefined,
) {
  if (!gaiaMatch) {
    return;
  }
  rows.push({
    id: "sel-gaia-match",
    label: "Gaia",
    value: gaiaMatch.gaia_match ? "Con contraparte" : "Sin contraparte",
    help: "Si esta detección coincide con una fuente del catálogo Gaia.",
    glossaryId: "gaia",
  });
  const separation = gaiaMatch.gaia_separation_arcsec;
  if (separation !== null && separation !== undefined) {
    rows.push({
      id: "sel-gaia-separation",
      label: "Separación",
      value: `${separation.toFixed(2)}″`,
      help: "Distancia angular entre la detección y la fuente Gaia más cercana.",
      glossaryId: "radio-cruce",
    });
  }
  rows.push({
    id: "sel-gaia-probability",
    label: "Probabilidad",
    value: `${Math.round((gaiaMatch.gaia_probability ?? 0) * 100)}%`,
    help: "Qué tan probable es que la contraparte Gaia sea correcta. Baja con la separación y llega a 0 fuera del radio de cruce.",
    glossaryId: "exponente-probabilidad",
  });
  if (gaiaMatch.gaia_source_id) {
    rows.push({
      id: "sel-gaia-id",
      label: "Gaia source",
      value: gaiaMatch.gaia_source_id,
      help: "Identificador de la fuente Gaia asociada.",
      glossaryId: "gaia",
    });
  }
}

export function formatSelectionNumber(
  value: number | null | undefined,
  digits = 4,
): string | null {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }
  return value.toPrecision(digits);
}
