import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import {
  type BestPreset,
  bestPresetExtendedParams,
  bestPresetPointParams,
  bestPresetSummary,
} from "../best-preset";
import { formatQueryError } from "../format-query-error";
import { CUSTOM_PRESET_ID, matchNamedPreset } from "../named-preset";
import {
  DEFAULT_EXTENDED_DETECTION_PARAMS,
  DEFAULT_POINT_DETECTION_PARAMS,
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
  type SourceDetectionDraft,
  sourceDetectionDraftSchema,
} from "../source-detection-fields";
import { DetectionFieldInput } from "./detection-field-input";
import { NamedPresetField } from "./named-preset-field";

type SourceDetectionFormProps = {
  isPending: boolean;
  bestPreset?: BestPreset;
  onSubmit: (params: SourceDetectionParams) => void;
};

function defaultDraft(): SourceDetectionDraft {
  return {
    ...pointToDraft(DEFAULT_POINT_DETECTION_PARAMS),
    ...extendedToDraft(DEFAULT_EXTENDED_DETECTION_PARAMS),
  };
}

function initialNamedPresetId() {
  const matched = matchNamedPreset(
    POINT_DETECTION_PRESETS,
    DEFAULT_POINT_DETECTION_PARAMS,
  );
  return matched === CUSTOM_PRESET_ID
    ? (POINT_DETECTION_PRESETS[0]?.id ?? CUSTOM_PRESET_ID)
    : matched;
}

export function SourceDetectionForm({
  isPending,
  bestPreset,
  onSubmit,
}: Readonly<SourceDetectionFormProps>) {
  const { watch, getValues, setValues, handleSubmit, reset } =
    useForm<SourceDetectionDraft>({
      resolver: zodResolver(sourceDetectionDraftSchema),
      defaultValues: defaultDraft(),
      mode: "onChange",
    });
  const draft = watch();
  const pointParams = parsePointDraft(draft);
  const presetId =
    pointParams === null
      ? CUSTOM_PRESET_ID
      : matchNamedPreset(POINT_DETECTION_PRESETS, pointParams);
  const [lastNamedId, setLastNamedId] = useState(initialNamedPresetId);

  function updateDraftValue<K extends keyof SourceDetectionDraft>(
    key: K,
    value: SourceDetectionDraft[K],
  ) {
    const next = { ...getValues(), [key]: value };
    setValues((current) => ({ ...current, [key]: value }), {
      shouldValidate: true,
      shouldDirty: true,
    });
    const nextPoint = parsePointDraft(next);
    if (nextPoint !== null) {
      const matched = matchNamedPreset(POINT_DETECTION_PRESETS, nextPoint);
      if (matched !== CUSTOM_PRESET_ID) {
        setLastNamedId(matched);
      }
    }
  }

  async function handleBestPreset() {
    const measured = await bestPreset?.request();
    if (measured === undefined) {
      return;
    }
    const currentDraft = getValues();
    const current = {
      ...(parsePointDraft(currentDraft) ?? DEFAULT_POINT_DETECTION_PARAMS),
      ...(parseExtendedDraft(currentDraft) ??
        DEFAULT_EXTENDED_DETECTION_PARAMS),
    };
    const nextPoint = bestPresetPointParams(
      measured,
      pointDetectionParams(current),
    );
    const nextExtended = bestPresetExtendedParams(
      measured,
      extendedDetectionParams(current),
    );
    reset({
      ...currentDraft,
      ...pointToDraft(nextPoint),
      ...extendedToDraft(nextExtended),
    });
    const matched = matchNamedPreset(POINT_DETECTION_PRESETS, nextPoint);
    if (matched !== CUSTOM_PRESET_ID) {
      setLastNamedId(matched);
    }
  }

  const submitForm = handleSubmit((values) => {
    const point = parsePointDraft(values);
    const extended = parseExtendedDraft(values);
    if (point === null || extended === null) {
      return;
    }
    onSubmit({ ...point, ...extended });
  });

  return (
    <form
      data-testid="source-detection-form"
      className="flex flex-col gap-4"
      onSubmit={submitForm}
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
            setLastNamedId(preset.id);
            reset({
              ...getValues(),
              ...pointToDraft(preset.values),
            });
          }}
        />
        {bestPreset !== undefined ? (
          <div className="flex flex-col gap-1">
            <Button
              type="button"
              variant="outline"
              data-testid="source-best-preset"
              disabled={isPending || bestPreset.isPending}
              onClick={() => {
                void handleBestPreset().catch((error) =>
                  toast.error(formatQueryError(error)),
                );
              }}
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
                updateDraftValue(field.key, nextValue);
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
              value={draft[field.key]}
              isPending={isPending}
              onValueChange={(nextValue) => {
                updateDraftValue(field.key, nextValue);
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
            reset(defaultDraft());
            setLastNamedId(initialNamedPresetId());
          }}
        >
          Restablecer
        </Button>
      </div>
    </form>
  );
}
