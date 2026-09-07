import { type SyntheticEvent, useState } from "react";
import type { DetectSourcesParams } from "@/api/generated/model";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import { CUSTOM_PRESET_ID, matchNamedPreset } from "../named-preset";
import {
  DEFAULT_SOURCE_DETECTION_PARAMS,
  SOURCE_DETECTION_PRESETS,
  type SourceDetectionParams,
} from "../source-detection";
import { NamedPresetField } from "./named-preset-field";

type SourceDetectionFormProps = {
  isPending: boolean;
  onSubmit: (params: Omit<DetectSourcesParams, "hdu">) => void;
};

type FieldKey = keyof SourceDetectionParams;

const FIELDS: { key: FieldKey; label: string; step: string; help: string }[] = [
  {
    key: "fwhm",
    label: "FWHM",
    step: "0.1",
    help: "Ancho a media altura del núcleo estelar, en píxeles. Valores más altos buscan estrellas más extendidas.",
  },
  {
    key: "sigma",
    label: "Sigma",
    step: "0.1",
    help: "Umbral de detección en RMS del fondo. Más alto exige picos más contrastados y suele devolver menos fuentes.",
  },
  {
    key: "min_snr",
    label: "SNR mínimo",
    step: "0.1",
    help: "Relación señal/ruido mínima para conservar un pico. Por debajo de este valor se descarta.",
  },
  {
    key: "min_score",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) que mezcla aspecto visual y forma. Filtra candidatos poco convincentes.",
  },
  {
    key: "min_distance",
    label: "Distancia mínima",
    step: "0.1",
    help: "Separación mínima entre picos, en píxeles. Evita marcar dos veces la misma estrella.",
  },
  {
    key: "visual_weight",
    label: "Peso visual",
    step: "0.05",
    help: "Cuánto pesa el aspecto visual frente a la morfología al calcular el score (0 = solo forma, 1 = solo visual).",
  },
  {
    key: "visual_area_radius",
    label: "Radio visual",
    step: "0.1",
    help: "Radio en píxeles del parche alrededor del pico usado para medir área, flujo y pico aparentes.",
  },
  {
    key: "visual_area_sigma",
    label: "Sigma visual",
    step: "0.1",
    help: "Umbral local del parche visual, en RMS del fondo. Define qué píxeles cuentan como parte de la fuente.",
  },
  {
    key: "max_sources",
    label: "Máximo de fuentes",
    step: "1",
    help: "Tope de fuentes a devolver, ordenadas por relevancia. 0 significa sin límite.",
  },
];

function paramsToDraft(
  params: SourceDetectionParams,
): Record<FieldKey, string> {
  return {
    fwhm: String(params.fwhm),
    sigma: String(params.sigma),
    min_snr: String(params.min_snr),
    min_score: String(params.min_score),
    min_distance: String(params.min_distance),
    visual_weight: String(params.visual_weight),
    visual_area_radius: String(params.visual_area_radius),
    visual_area_sigma: String(params.visual_area_sigma),
    max_sources: String(params.max_sources),
  };
}

function parseDraft(
  draft: Record<FieldKey, string>,
): SourceDetectionParams | null {
  const parsed: Partial<SourceDetectionParams> = {};
  for (const field of FIELDS) {
    const raw = draft[field.key].trim();
    if (raw === "") {
      return null;
    }
    const numeric = Number(raw);
    if (!Number.isFinite(numeric)) {
      return null;
    }
    parsed[field.key] = numeric;
  }
  return {
    ...(parsed as SourceDetectionParams),
    max_sources: Math.round(parsed.max_sources ?? 0),
  };
}

export function SourceDetectionForm({
  isPending,
  onSubmit,
}: Readonly<SourceDetectionFormProps>) {
  const [draft, setDraft] = useState(() =>
    paramsToDraft(DEFAULT_SOURCE_DETECTION_PARAMS),
  );
  const [presetId, setPresetId] = useState(() =>
    matchNamedPreset(SOURCE_DETECTION_PRESETS, DEFAULT_SOURCE_DETECTION_PARAMS),
  );
  const [lastNamedId, setLastNamedId] = useState("estandar");

  function applyValues(values: SourceDetectionParams) {
    setDraft(paramsToDraft(values));
    const matched = matchNamedPreset(SOURCE_DETECTION_PRESETS, values);
    setPresetId(matched);
    if (matched !== CUSTOM_PRESET_ID) {
      setLastNamedId(matched);
    }
  }

  function updateField(key: FieldKey, nextValue: string) {
    const nextDraft = { ...draft, [key]: nextValue };
    setDraft(nextDraft);
    const parsed = parseDraft(nextDraft);
    if (parsed === null) {
      setPresetId(CUSTOM_PRESET_ID);
      return;
    }
    const matched = matchNamedPreset(SOURCE_DETECTION_PRESETS, parsed);
    setPresetId(matched);
    if (matched !== CUSTOM_PRESET_ID) {
      setLastNamedId(matched);
    }
  }

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = parseDraft(draft);
    if (values === null) {
      return;
    }
    onSubmit(values);
  }

  return (
    <form
      data-testid="source-detection-form"
      className="flex flex-col gap-4"
      onSubmit={handleSubmit}
    >
      <NamedPresetField
        label="Preset"
        testId="source-preset"
        presets={SOURCE_DETECTION_PRESETS}
        value={presetId}
        lastNamedId={lastNamedId}
        disabled={isPending}
        onSelect={(preset) => {
          applyValues(preset.values);
        }}
      />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {FIELDS.map((field) => (
          <div key={field.key} className="flex flex-col gap-1 text-sm">
            <div className="flex items-center gap-1">
              <label htmlFor={field.key} className="text-muted-foreground">
                {field.label}
              </label>
              <HelpHint label={field.label} testId={`source-help-${field.key}`}>
                {field.help}
              </HelpHint>
            </div>
            <Input
              id={field.key}
              data-testid={`source-field-${field.key}`}
              type="number"
              step={field.step}
              value={draft[field.key]}
              disabled={isPending}
              onChange={(event) => {
                updateField(field.key, event.target.value);
              }}
            />
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          type="submit"
          data-testid="source-detect-submit"
          disabled={isPending}
        >
          {isPending ? "Detectando…" : "Detectar fuentes"}
        </Button>
        <Button
          type="button"
          variant="outline"
          data-testid="source-detect-reset"
          disabled={isPending}
          onClick={() => {
            applyValues(DEFAULT_SOURCE_DETECTION_PARAMS);
          }}
        >
          Restablecer
        </Button>
      </div>
    </form>
  );
}
