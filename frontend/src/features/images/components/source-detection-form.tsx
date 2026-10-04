import type { SyntheticEvent } from "react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import {
  type BestPreset,
  bestPresetExtendedParams,
  bestPresetPointParams,
  bestPresetSummary,
} from "../best-preset";
import {
  DEFAULT_EXTENDED_DETECTION_PARAMS,
  DEFAULT_POINT_DETECTION_PARAMS,
  DEFAULT_SOURCE_DETECTION_PARAMS,
  type ExtendedDetectionParams,
  extendedDetectionParams,
  POINT_DETECTION_PRESETS,
  type PointDetectionParams,
  pointDetectionParams,
  type SourceDetectionParams,
} from "../source-detection";
import { useNamedPresetDraft } from "../use-named-preset-draft";
import { DecimalInput } from "./decimal-input";
import { NamedPresetField } from "./named-preset-field";

type SourceDetectionFormProps = {
  isPending: boolean;
  bestPreset?: BestPreset;
  onSubmit: (params: SourceDetectionParams) => void;
};

type DetectionField<K extends string> = {
  key: K;
  label: string;
  step: string;
  help: string;
  glossaryId: string;
};

const POINT_FIELDS: DetectionField<keyof PointDetectionParams>[] = [
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

const EXTENDED_FIELDS: DetectionField<keyof ExtendedDetectionParams>[] = [
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
    glossaryId: "score",
  },
  {
    key: "ext_max_sources",
    label: "Máximo de estructuras",
    step: "1",
    help: "Tope de estructuras a devolver, ordenadas por relevancia. 0 significa sin límite.",
    glossaryId: "max-sources",
  },
];

function pointToDraft(
  params: PointDetectionParams,
): Record<keyof PointDetectionParams, string> {
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

function extendedToDraft(
  params: ExtendedDetectionParams,
): Record<keyof ExtendedDetectionParams, string> {
  return {
    ext_sigma: String(params.ext_sigma),
    ext_smooth_sigma: String(params.ext_smooth_sigma),
    ext_min_area: String(params.ext_min_area),
    ext_max_area: String(params.ext_max_area),
    ext_bin_factor: String(params.ext_bin_factor),
    ext_closing_iterations: String(params.ext_closing_iterations),
    ext_opening_iterations: String(params.ext_opening_iterations),
    ext_min_score: String(params.ext_min_score),
    ext_max_sources: String(params.ext_max_sources),
  };
}

function parsePointDraft(
  draft: Record<keyof PointDetectionParams, string>,
): PointDetectionParams | null {
  const fwhm = readNumber(draft.fwhm);
  const sigma = readNumber(draft.sigma);
  const minSnr = readNumber(draft.min_snr);
  const minScore = readNumber(draft.min_score);
  const minDistance = readNumber(draft.min_distance);
  const visualWeight = readNumber(draft.visual_weight);
  const visualAreaRadius = readNumber(draft.visual_area_radius);
  const visualAreaSigma = readNumber(draft.visual_area_sigma);
  const maxSources = readNumber(draft.max_sources);
  if (
    fwhm === null ||
    sigma === null ||
    minSnr === null ||
    minScore === null ||
    minDistance === null ||
    visualWeight === null ||
    visualAreaRadius === null ||
    visualAreaSigma === null ||
    maxSources === null
  ) {
    return null;
  }
  return {
    fwhm,
    sigma,
    min_snr: minSnr,
    min_score: minScore,
    min_distance: minDistance,
    visual_weight: visualWeight,
    visual_area_radius: visualAreaRadius,
    visual_area_sigma: visualAreaSigma,
    max_sources: Math.round(maxSources),
  };
}

function parseExtendedDraft(
  draft: Record<keyof ExtendedDetectionParams, string>,
): ExtendedDetectionParams | null {
  const extSigma = readNumber(draft.ext_sigma);
  const extSmoothSigma = readNumber(draft.ext_smooth_sigma);
  const extMinArea = readNumber(draft.ext_min_area);
  const extMaxArea = readNumber(draft.ext_max_area);
  const extBinFactor = readNumber(draft.ext_bin_factor);
  const extClosing = readNumber(draft.ext_closing_iterations);
  const extOpening = readNumber(draft.ext_opening_iterations);
  const extMinScore = readNumber(draft.ext_min_score);
  const extMaxSources = readNumber(draft.ext_max_sources);
  if (
    extSigma === null ||
    extSmoothSigma === null ||
    extMinArea === null ||
    extMaxArea === null ||
    extBinFactor === null ||
    extClosing === null ||
    extOpening === null ||
    extMinScore === null ||
    extMaxSources === null
  ) {
    return null;
  }
  return {
    ext_sigma: extSigma,
    ext_smooth_sigma: extSmoothSigma,
    ext_min_area: Math.round(extMinArea),
    ext_max_area: Math.round(extMaxArea),
    ext_bin_factor: Math.round(extBinFactor),
    ext_closing_iterations: Math.round(extClosing),
    ext_opening_iterations: Math.round(extOpening),
    ext_min_score: extMinScore,
    ext_max_sources: Math.round(extMaxSources),
  };
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
  bestPreset,
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
  const measured = bestPreset?.data;
  const [appliedMeasurement, setAppliedMeasurement] =
    useState<typeof measured>(undefined);
  const currentValues = useRef<SourceDetectionParams>(
    DEFAULT_SOURCE_DETECTION_PARAMS,
  );
  currentValues.current = {
    ...(parseDraft() ?? DEFAULT_POINT_DETECTION_PARAMS),
    ...(parseExtendedDraft(extendedDraft) ?? DEFAULT_EXTENDED_DETECTION_PARAMS),
  };
  if (measured !== undefined && measured !== appliedMeasurement) {
    setAppliedMeasurement(measured);
    applyParams(
      bestPresetPointParams(
        measured,
        pointDetectionParams(currentValues.current),
      ),
    );
    setExtendedDraft(
      extendedToDraft(
        bestPresetExtendedParams(
          measured,
          extendedDetectionParams(currentValues.current),
        ),
      ),
    );
  }

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
        {bestPreset !== undefined ? (
          <div className="flex flex-col gap-1">
            <Button
              type="button"
              variant="outline"
              data-testid="source-best-preset"
              disabled={isPending || bestPreset.isPending}
              onClick={bestPreset.request}
            >
              {bestPreset.isPending ? "Midiendo…" : "Usar el recomendado"}
            </Button>
            <div className="flex items-center gap-1">
              <HelpHint
                label="preset recomendado"
                testId="source-help-best-preset"
                glossaryId="preset-recomendado"
              >
                Mide el núcleo de las fuentes que ya detectaste en esta imagen y
                ajusta los valores que dependen de ese ancho. El resto los deja
                como están.
              </HelpHint>
              <p
                data-testid="source-best-preset-summary"
                className="text-muted-foreground text-xs leading-snug"
              >
                {bestPreset.isError
                  ? "No se pudo pedir el recomendado a la API."
                  : bestPresetSummary(bestPreset.data?.evidence)}
              </p>
            </div>
          </div>
        ) : null}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {POINT_FIELDS.map((field) => (
            <FieldInput
              key={field.key}
              field={field}
              value={draft[field.key]}
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
              value={extendedDraft[field.key]}
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
  field: DetectionField<string>;
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
