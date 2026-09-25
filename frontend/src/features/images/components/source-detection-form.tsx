import type { SyntheticEvent } from "react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import {
  DEFAULT_EXTENDED_DETECTION_PARAMS,
  DEFAULT_POINT_DETECTION_PARAMS,
  EXTENDED_DETECTION_KEYS,
  type ExtendedDetectionParams,
  POINT_DETECTION_KEYS,
  POINT_DETECTION_PRESETS,
  type PointDetectionParams,
  type SourceDetectionParams,
} from "../source-detection";
import { useNamedPresetDraft } from "../use-named-preset-draft";
import { DecimalInput } from "./decimal-input";
import { NamedPresetField } from "./named-preset-field";

type SourceDetectionFormProps = {
  isPending: boolean;
  onSubmit: (params: SourceDetectionParams) => void;
};

type FieldDefinition = {
  key: keyof SourceDetectionParams;
  label: string;
  step: string;
  help: string;
  glossaryId?: string;
};

const POINT_FIELDS: FieldDefinition[] = [
  {
    key: "fwhm",
    label: "FWHM",
    step: "0.1",
    help: "Ancho a media altura del núcleo estelar, en píxeles. Valores más altos buscan estrellas más extendidas.",
    glossaryId: "fwhm",
  },
  {
    key: "sigma",
    label: "Sigma",
    step: "0.1",
    help: "Umbral de detección en RMS del fondo. Más alto exige picos más contrastados y suele devolver menos fuentes.",
    glossaryId: "sigma",
  },
  {
    key: "min_snr",
    label: "SNR mínimo",
    step: "0.1",
    help: "Relación señal/ruido mínima para conservar un pico. Por debajo de este valor se descarta.",
    glossaryId: "snr",
  },
  {
    key: "min_score",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) que mezcla aspecto visual y forma. Filtra candidatos poco convincentes.",
    glossaryId: "score",
  },
  {
    key: "min_distance",
    label: "Distancia mínima",
    step: "0.1",
    help: "Separación mínima entre picos, en píxeles. Evita marcar dos veces la misma estrella.",
    glossaryId: "min-distance",
  },
  {
    key: "visual_weight",
    label: "Peso visual",
    step: "0.05",
    help: "Cuánto pesa el aspecto visual frente a la morfología al calcular el score (0 = solo forma, 1 = solo visual).",
    glossaryId: "visual-weight",
  },
  {
    key: "visual_area_radius",
    label: "Radio visual",
    step: "0.1",
    help: "Radio en píxeles del parche alrededor del pico usado para medir área, flujo y pico aparentes.",
    glossaryId: "visual-area-radius",
  },
  {
    key: "visual_area_sigma",
    label: "Sigma visual",
    step: "0.1",
    help: "Umbral local del parche visual, en RMS del fondo. Define qué píxeles cuentan como parte de la fuente.",
    glossaryId: "visual-area-sigma",
  },
  {
    key: "max_sources",
    label: "Máximo de fuentes",
    step: "1",
    help: "Tope de fuentes a devolver, ordenadas por relevancia. 0 significa sin límite.",
    glossaryId: "max-sources",
  },
];

const EXTENDED_FIELDS: FieldDefinition[] = [
  {
    key: "ext_sigma",
    label: "Sigma",
    step: "0.1",
    help: "Umbral en RMS del fondo para abrir regiones. Más alto exige nebulosas más contrastadas.",
    glossaryId: "ext-sigma",
  },
  {
    key: "ext_smooth_sigma",
    label: "Suavizado",
    step: "0.1",
    help: "Suavizado gaussiano previo en píxeles. Muy bajo deja ruido; muy alto funde estructuras finas.",
    glossaryId: "ext-smooth-sigma",
  },
  {
    key: "ext_min_area",
    label: "Área mínima",
    step: "10",
    help: "Área mínima de la región en píxeles. Estructuras más chicas se descartan.",
    glossaryId: "ext-min-area",
  },
  {
    key: "ext_max_area",
    label: "Área máxima",
    step: "10",
    help: "Área máxima de la región en píxeles. 0 significa sin límite.",
    glossaryId: "ext-max-area",
  },
  {
    key: "ext_bin_factor",
    label: "Factor de bin",
    step: "1",
    help: "Agrupado de píxeles que hace el detector. No cambia el resultado, solo el costo.",
    glossaryId: "ext-binning",
  },
  {
    key: "ext_closing_iterations",
    label: "Cierre",
    step: "1",
    help: "Pasadas de cierre morfológico que rellenan huecos y unen bordes. 0 desactiva.",
    glossaryId: "ext-closing",
  },
  {
    key: "ext_opening_iterations",
    label: "Apertura",
    step: "1",
    help: "Pasadas de apertura que cortan protuberancias finas y ruido. 0 desactiva.",
    glossaryId: "ext-opening",
  },
  {
    key: "ext_min_score",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) mínima para conservar una estructura.",
  },
  {
    key: "ext_max_sources",
    label: "Máximo de estructuras",
    step: "1",
    help: "Tope de estructuras a devolver, ordenadas por relevancia. 0 significa sin límite.",
  },
];

const INTEGER_EXTENDED_KEYS = [
  "ext_max_sources",
  "ext_min_area",
  "ext_max_area",
  "ext_bin_factor",
  "ext_closing_iterations",
  "ext_opening_iterations",
] as const;

function pointToDraft(
  params: PointDetectionParams,
): Record<keyof PointDetectionParams, string> {
  const draft = {} as Record<keyof PointDetectionParams, string>;
  for (const key of POINT_DETECTION_KEYS) {
    draft[key] = String(params[key]);
  }
  return draft;
}

function extendedToDraft(
  params: ExtendedDetectionParams,
): Record<keyof ExtendedDetectionParams, string> {
  const draft = {} as Record<keyof ExtendedDetectionParams, string>;
  for (const key of EXTENDED_DETECTION_KEYS) {
    draft[key] = String(params[key]);
  }
  return draft;
}

function parsePointDraft(
  draft: Record<keyof PointDetectionParams, string>,
): PointDetectionParams | null {
  const parsed: Partial<PointDetectionParams> = {};
  for (const key of POINT_DETECTION_KEYS) {
    const numeric = readNumber(draft[key]);
    if (numeric === null) {
      return null;
    }
    parsed[key] = numeric;
  }
  return {
    ...(parsed as PointDetectionParams),
    max_sources: Math.round(parsed.max_sources ?? 0),
  };
}

function parseExtendedDraft(
  draft: Record<keyof ExtendedDetectionParams, string>,
): ExtendedDetectionParams | null {
  const parsed: Partial<ExtendedDetectionParams> = {};
  for (const key of EXTENDED_DETECTION_KEYS) {
    const numeric = readNumber(draft[key]);
    if (numeric === null) {
      return null;
    }
    parsed[key] = isIntegerExtendedKey(key) ? Math.round(numeric) : numeric;
  }
  return parsed as ExtendedDetectionParams;
}

function isIntegerExtendedKey(
  key: keyof ExtendedDetectionParams,
): key is (typeof INTEGER_EXTENDED_KEYS)[number] {
  return INTEGER_EXTENDED_KEYS.includes(
    key as (typeof INTEGER_EXTENDED_KEYS)[number],
  );
}

function readNumber(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return null;
  }
  const numeric = Number(trimmed);
  return Number.isFinite(numeric) ? numeric : null;
}

export function SourceDetectionForm({
  isPending,
  onSubmit,
}: Readonly<SourceDetectionFormProps>) {
  const { draft, presetId, lastNamedId, applyParams, applyDraft, parseDraft } =
    useNamedPresetDraft({
      presets: POINT_DETECTION_PRESETS,
      defaults: DEFAULT_POINT_DETECTION_PARAMS,
      toDraft: pointToDraft,
      parseDraft: parsePointDraft,
    });
  const [extendedDraft, setExtendedDraft] = useState(() =>
    extendedToDraft(DEFAULT_EXTENDED_DETECTION_PARAMS),
  );

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const point = parseDraft();
    const extended = parseExtendedDraft(extendedDraft);
    if (point === null || extended === null) {
      return;
    }
    onSubmit({ ...point, ...extended });
  }

  return (
    <form
      data-testid="source-detection-form"
      className="flex flex-col gap-4"
      onSubmit={handleSubmit}
    >
      <section
        data-testid="source-group-point"
        className="flex flex-col gap-3 rounded-md border border-border p-3"
      >
        <div className="flex items-center gap-1">
          <h3 className="text-sm font-semibold text-foreground">
            Puntos simples
          </h3>
          <HelpHint
            label="Puntos simples"
            testId="source-help-group-point"
            glossaryId="fuente-puntual"
          >
            Estrellas y picos nítidos. Se marcan con puntos. El preset solo
            rellena estos valores.
          </HelpHint>
        </div>
        <NamedPresetField
          label="Preset de puntos"
          testId="source-preset"
          glossaryId="preset-deteccion"
          presets={POINT_DETECTION_PRESETS}
          value={presetId}
          lastNamedId={lastNamedId}
          disabled={isPending}
          onSelect={(preset) => {
            applyParams(preset.values);
          }}
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {POINT_FIELDS.map((field) => (
            <FieldInput
              key={field.key}
              field={field}
              value={draft[field.key as keyof PointDetectionParams]}
              isPending={isPending}
              onValueChange={(nextValue) => {
                applyDraft({
                  ...draft,
                  [field.key]: nextValue,
                });
              }}
            />
          ))}
        </div>
      </section>
      <section
        data-testid="source-group-extended"
        className="flex flex-col gap-3 rounded-md border border-border p-3"
      >
        <div className="flex items-center gap-1">
          <h3 className="text-sm font-semibold text-foreground">
            Fuentes extendidas
          </h3>
          <HelpHint
            label="Fuentes extendidas"
            testId="source-help-group-extended"
            glossaryId="fuente-extendida"
          >
            Nebulosas y galaxias. Se marcan con recuadros sobre el visor.
          </HelpHint>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {EXTENDED_FIELDS.map((field) => (
            <FieldInput
              key={field.key}
              field={field}
              value={extendedDraft[field.key as keyof ExtendedDetectionParams]}
              isPending={isPending}
              onValueChange={(nextValue) => {
                setExtendedDraft((current) => ({
                  ...current,
                  [field.key]: nextValue,
                }));
              }}
            />
          ))}
        </div>
      </section>
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
            applyParams(DEFAULT_POINT_DETECTION_PARAMS);
            setExtendedDraft(
              extendedToDraft(DEFAULT_EXTENDED_DETECTION_PARAMS),
            );
          }}
        >
          Restablecer
        </Button>
      </div>
    </form>
  );
}

function FieldInput({
  field,
  value,
  isPending,
  onValueChange,
}: Readonly<{
  field: FieldDefinition;
  value: string;
  isPending: boolean;
  onValueChange: (value: string) => void;
}>) {
  return (
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex items-center gap-1">
        <label htmlFor={field.key} className="text-muted-foreground">
          {field.label}
        </label>
        <HelpHint
          label={field.label}
          testId={`source-help-${field.key}`}
          glossaryId={field.glossaryId}
        >
          {field.help}
        </HelpHint>
      </div>
      <DecimalInput
        id={field.key}
        testId={`source-field-${field.key}`}
        step={field.step}
        value={value}
        disabled={isPending}
        onValueChange={onValueChange}
      />
    </div>
  );
}
