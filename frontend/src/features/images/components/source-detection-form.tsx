import { type SyntheticEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import { CUSTOM_PRESET_ID, matchNamedPreset } from "../named-preset";
import {
  DEFAULT_SOURCE_DETECTION_PARAMS,
  POINT_DETECTION_PRESETS,
  type PointDetectionParams,
  pointDetectionParams,
  type SourceDetectionParams,
} from "../source-detection";
import { NamedPresetField } from "./named-preset-field";

type SourceDetectionFormProps = {
  isPending: boolean;
  onSubmit: (params: SourceDetectionParams) => void;
};

type FieldKey = keyof SourceDetectionParams;
type GroupId = "point" | "extended";

type FieldDefinition = {
  key: FieldKey;
  group: GroupId;
  label: string;
  step: string;
  help: string;
  glossaryId?: string;
};

const FIELDS: FieldDefinition[] = [
  {
    key: "fwhm",
    group: "point",
    label: "FWHM",
    step: "0.1",
    help: "Ancho a media altura del núcleo estelar, en píxeles. Valores más altos buscan estrellas más extendidas.",
  },
  {
    key: "sigma",
    group: "point",
    label: "Sigma",
    step: "0.1",
    help: "Umbral de detección en RMS del fondo. Más alto exige picos más contrastados y suele devolver menos fuentes.",
  },
  {
    key: "min_snr",
    group: "point",
    label: "SNR mínimo",
    step: "0.1",
    help: "Relación señal/ruido mínima para conservar un pico. Por debajo de este valor se descarta.",
  },
  {
    key: "min_score",
    group: "point",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) que mezcla aspecto visual y forma. Filtra candidatos poco convincentes.",
  },
  {
    key: "min_distance",
    group: "point",
    label: "Distancia mínima",
    step: "0.1",
    help: "Separación mínima entre picos, en píxeles. Evita marcar dos veces la misma estrella.",
  },
  {
    key: "visual_weight",
    group: "point",
    label: "Peso visual",
    step: "0.05",
    help: "Cuánto pesa el aspecto visual frente a la morfología al calcular el score (0 = solo forma, 1 = solo visual).",
  },
  {
    key: "visual_area_radius",
    group: "point",
    label: "Radio visual",
    step: "0.1",
    help: "Radio en píxeles del parche alrededor del pico usado para medir área, flujo y pico aparentes.",
  },
  {
    key: "visual_area_sigma",
    group: "point",
    label: "Sigma visual",
    step: "0.1",
    help: "Umbral local del parche visual, en RMS del fondo. Define qué píxeles cuentan como parte de la fuente.",
  },
  {
    key: "max_sources",
    group: "point",
    label: "Máximo de fuentes",
    step: "1",
    help: "Tope de fuentes a devolver, ordenadas por relevancia. 0 significa sin límite.",
  },
  {
    key: "ext_sigma",
    group: "extended",
    label: "Sigma",
    step: "0.1",
    help: "Umbral en RMS del fondo para abrir regiones. Más alto exige nebulosas más contrastadas.",
    glossaryId: "ext-sigma",
  },
  {
    key: "ext_smooth_sigma",
    group: "extended",
    label: "Suavizado",
    step: "0.1",
    help: "Suavizado gaussiano previo en píxeles. Muy bajo deja ruido; muy alto funde estructuras finas.",
    glossaryId: "ext-smooth-sigma",
  },
  {
    key: "ext_min_area",
    group: "extended",
    label: "Área mínima",
    step: "10",
    help: "Área mínima de la región en píxeles. Estructuras más chicas se descartan.",
    glossaryId: "ext-min-area",
  },
  {
    key: "ext_max_area",
    group: "extended",
    label: "Área máxima",
    step: "10",
    help: "Área máxima de la región en píxeles. 0 significa sin límite.",
    glossaryId: "ext-max-area",
  },
  {
    key: "ext_bin_factor",
    group: "extended",
    label: "Factor de bin",
    step: "1",
    help: "Agrupado de píxeles que hace el detector. No cambia el resultado, solo el costo.",
    glossaryId: "ext-binning",
  },
  {
    key: "ext_closing_iterations",
    group: "extended",
    label: "Cierre",
    step: "1",
    help: "Pasadas de cierre morfológico que rellenan huecos y unen bordes. 0 desactiva.",
    glossaryId: "ext-closing",
  },
  {
    key: "ext_opening_iterations",
    group: "extended",
    label: "Apertura",
    step: "1",
    help: "Pasadas de apertura que cortan protuberancias finas y ruido. 0 desactiva.",
    glossaryId: "ext-opening",
  },
  {
    key: "ext_min_score",
    group: "extended",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) mínima para conservar una estructura.",
  },
  {
    key: "ext_max_sources",
    group: "extended",
    label: "Máximo de estructuras",
    step: "1",
    help: "Tope de estructuras a devolver, ordenadas por relevancia. 0 significa sin límite.",
  },
];

function paramsToDraft(
  params: SourceDetectionParams,
): Record<FieldKey, string> {
  const draft = {} as Record<FieldKey, string>;
  for (const field of FIELDS) {
    draft[field.key] = String(params[field.key]);
  }
  return draft;
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
    ext_max_sources: Math.round(parsed.ext_max_sources ?? 0),
    ext_min_area: Math.round(parsed.ext_min_area ?? 0),
    ext_max_area: Math.round(parsed.ext_max_area ?? 0),
    ext_bin_factor: Math.round(parsed.ext_bin_factor ?? 0),
    ext_closing_iterations: Math.round(parsed.ext_closing_iterations ?? 0),
    ext_opening_iterations: Math.round(parsed.ext_opening_iterations ?? 0),
  };
}

function matchPointPreset(values: PointDetectionParams): {
  matched: string;
  lastNamedId: string;
} {
  const matched = matchNamedPreset(POINT_DETECTION_PRESETS, values);
  if (matched === CUSTOM_PRESET_ID) {
    return { matched, lastNamedId: "" };
  }
  return { matched, lastNamedId: matched };
}

export function SourceDetectionForm({
  isPending,
  onSubmit,
}: Readonly<SourceDetectionFormProps>) {
  const defaults = DEFAULT_SOURCE_DETECTION_PARAMS;
  const defaultPreset = matchPointPreset(pointDetectionParams(defaults));
  const [draft, setDraft] = useState<Record<FieldKey, string>>(() =>
    paramsToDraft(defaults),
  );
  const [presetId, setPresetId] = useState(defaultPreset.matched);
  const [lastNamedId, setLastNamedId] = useState(defaultPreset.lastNamedId);

  function valuesOf(draftValue: Record<FieldKey, string>) {
    return parseDraft(draftValue);
  }

  function updatePointPreset(draftValue: Record<FieldKey, string>) {
    const values = valuesOf(draftValue);
    const preset = matchPointPreset(pointDetectionParams(values ?? defaults));
    setPresetId(preset.matched);
    if (preset.lastNamedId !== "") {
      setLastNamedId(preset.lastNamedId);
    }
  }

  function applyValues(values: SourceDetectionParams) {
    setDraft(paramsToDraft(values));
    const preset = matchPointPreset(pointDetectionParams(values));
    setPresetId(preset.matched);
    if (preset.lastNamedId !== "") {
      setLastNamedId(preset.lastNamedId);
    }
  }

  function updateField(key: FieldKey, nextValue: string) {
    const nextDraft = { ...draft, [key]: nextValue };
    setDraft(nextDraft);
    updatePointPreset(nextDraft);
  }

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = parseDraft(draft);
    if (values === null) {
      return;
    }
    onSubmit(values);
  }

  const pointFields = FIELDS.filter((field) => field.group === "point");
  const extendedFields = FIELDS.filter((field) => field.group === "extended");

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
            const current = valuesOf(draft) ?? DEFAULT_SOURCE_DETECTION_PARAMS;
            applyValues({
              ...current,
              ...preset.values,
            });
          }}
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {pointFields.map((field) => (
            <FieldInput
              key={field.key}
              field={field}
              draft={draft}
              isPending={isPending}
              onChange={updateField}
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
          {extendedFields.map((field) => (
            <FieldInput
              key={field.key}
              field={field}
              draft={draft}
              isPending={isPending}
              onChange={updateField}
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
            applyValues(DEFAULT_SOURCE_DETECTION_PARAMS);
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
  draft,
  isPending,
  onChange,
}: Readonly<{
  field: FieldDefinition;
  draft: Record<FieldKey, string>;
  isPending: boolean;
  onChange: (key: FieldKey, value: string) => void;
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
      <Input
        id={field.key}
        data-testid={`source-field-${field.key}`}
        type="number"
        step={field.step}
        value={draft[field.key]}
        disabled={isPending}
        onChange={(event) => {
          onChange(field.key, event.target.value);
        }}
      />
    </div>
  );
}
