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
  extendedDetectionParams,
  POINT_DETECTION_PRESETS,
  pointDetectionParams,
  type SourceDetectionParams,
} from "../source-detection";
import {
  EXTENDED_FIELDS,
  extendedToDraft,
  POINT_FIELDS,
  parseExtendedDraft,
  parsePointDraft,
  pointToDraft,
} from "../source-detection-fields";
import { useNamedPresetDraft } from "../use-named-preset-draft";
import { DetectionFieldInput } from "./detection-field-input";
import { NamedPresetField } from "./named-preset-field";

type SourceDetectionFormProps = {
  isPending: boolean;
  bestPreset?: BestPreset;
  onSubmit: (params: SourceDetectionParams) => void;
};

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
            <DetectionFieldInput
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
            <DetectionFieldInput
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
