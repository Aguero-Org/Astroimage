import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { CUSTOM_PRESET_ID, matchNamedPreset } from "../named-preset";
import {
  COLORMAP_OPTIONS,
  DEFAULT_RENDER_PARAMS,
  LIMITS_OPTIONS,
  paramsToDraft,
  parseRenderDraft,
  RENDER_PRESETS,
  type RenderDraft,
  type RenderViewParams,
  renderDraftSchema,
  STRETCH_OPTIONS,
} from "../render-view";
import { DecimalInput } from "./decimal-input";
import { ExclusiveChoice } from "./exclusive-choice";
import { NamedPresetField } from "./named-preset-field";
import { RenderField } from "./render-field";

type RenderViewFormProps = {
  isPending: boolean;
  onSubmit: (params: RenderViewParams) => void;
};

function initialNamedPresetId() {
  const matched = matchNamedPreset(RENDER_PRESETS, DEFAULT_RENDER_PARAMS);
  return matched === CUSTOM_PRESET_ID
    ? (RENDER_PRESETS[0]?.id ?? CUSTOM_PRESET_ID)
    : matched;
}

export function RenderViewForm({
  isPending,
  onSubmit,
}: Readonly<RenderViewFormProps>) {
  const { watch, setValues, handleSubmit, reset } = useForm<RenderDraft>({
    resolver: zodResolver(renderDraftSchema),
    defaultValues: paramsToDraft(DEFAULT_RENDER_PARAMS),
    mode: "onChange",
  });
  const draft = watch();
  const parsedDraft = parseRenderDraft(draft);
  const presetId =
    parsedDraft === null
      ? CUSTOM_PRESET_ID
      : matchNamedPreset(RENDER_PRESETS, parsedDraft);
  const [lastNamedId, setLastNamedId] = useState(initialNamedPresetId);

  function updateDraftValue<K extends keyof RenderDraft>(
    key: K,
    value: RenderDraft[K],
  ) {
    const next = { ...watch(), [key]: value };
    setValues((current) => ({ ...current, [key]: value }), {
      shouldValidate: true,
      shouldDirty: true,
    });
    const parsed = parseRenderDraft(next);
    if (parsed !== null) {
      const matched = matchNamedPreset(RENDER_PRESETS, parsed);
      if (matched !== CUSTOM_PRESET_ID) {
        setLastNamedId(matched);
      }
    }
  }

  const submitForm = handleSubmit((values) => {
    const parsed = parseRenderDraft(values);
    if (parsed === null) {
      return;
    }
    onSubmit(parsed);
  });

  return (
    <form
      data-testid="render-view-form"
      className="flex flex-col gap-3"
      onSubmit={submitForm}
    >
      <NamedPresetField
        label="Preset"
        testId="render-preset"
        glossaryId="preset-vista"
        presets={RENDER_PRESETS}
        value={presetId}
        lastNamedId={lastNamedId}
        disabled={isPending}
        onSelect={(preset) => {
          setLastNamedId(preset.id);
          reset(paramsToDraft(preset.values));
        }}
      />
      <RenderField
        label="Stretch"
        testId="render-stretch"
        glossaryId="stretch"
        help="Cómo se comprime el brillo de los píxeles. Lineal deja el rango crudo; raíz y log resaltan estructura débil."
      >
        <ExclusiveChoice
          name="stretch"
          value={draft.stretch}
          options={STRETCH_OPTIONS}
          disabled={isPending}
          onChange={(stretch) => {
            updateDraftValue("stretch", stretch);
          }}
        />
      </RenderField>
      <RenderField
        label="Límites"
        testId="render-limits"
        glossaryId="limits"
        help="Cómo se elige el rango de intensidad. Percentiles recorta colas; ZScale se adapta al ruido local."
      >
        <ExclusiveChoice
          name="limits"
          value={draft.limits}
          options={LIMITS_OPTIONS}
          disabled={isPending}
          onChange={(limits) => {
            updateDraftValue("limits", limits);
          }}
        />
      </RenderField>
      <RenderField
        label="Mapa de color"
        testId="render-colormap"
        glossaryId="colormap"
        help="Paleta con la que se pinta el PNG. Gris es el default astronómico; las otras paletas resaltan contraste."
      >
        <ExclusiveChoice
          name="colormap"
          value={draft.colormap}
          options={COLORMAP_OPTIONS}
          disabled={isPending}
          onChange={(colormap) => {
            updateDraftValue("colormap", colormap);
          }}
        />
      </RenderField>
      <div className="grid grid-cols-2 gap-3">
        <RenderField
          label="Pmin"
          testId="render-pmin"
          glossaryId="pmin"
          help="Percentil inferior del recorte (0–100). Subirlo oculta fondo; debe ser menor que Pmax."
        >
          <DecimalInput
            id="render-pmin"
            testId="render-field-pmin"
            step="0.1"
            value={draft.pmin}
            disabled={isPending}
            onValueChange={(pmin) => {
              updateDraftValue("pmin", pmin);
            }}
          />
        </RenderField>
        <RenderField
          label="Pmax"
          testId="render-pmax"
          glossaryId="pmax"
          help="Percentil superior del recorte (0–100). Bajarlo satura menos las estrellas brillantes."
        >
          <DecimalInput
            id="render-pmax"
            testId="render-field-pmax"
            step="0.1"
            value={draft.pmax}
            disabled={isPending}
            onValueChange={(pmax) => {
              updateDraftValue("pmax", pmax);
            }}
          />
        </RenderField>
      </div>
      <RenderField
        label="Gamma"
        testId="render-gamma"
        glossaryId="gamma"
        help="Curva extra sobre el stretch (0.1–5). Mayor que 1 aclara medios tonos; menor que 1 los oscurece."
      >
        <DecimalInput
          id="render-gamma"
          testId="render-field-gamma"
          step="0.1"
          value={draft.gamma}
          disabled={isPending}
          onValueChange={(gamma) => {
            updateDraftValue("gamma", gamma);
          }}
        />
      </RenderField>
      <div className="flex flex-wrap gap-2">
        <Button
          type="submit"
          data-testid="render-view-submit"
          disabled={isPending}
        >
          {isPending ? "Renderizando…" : "Aplicar vista"}
        </Button>
        <Button
          type="button"
          variant="outline"
          data-testid="render-view-reset"
          disabled={isPending}
          onClick={() => {
            reset(paramsToDraft(DEFAULT_RENDER_PARAMS));
            setLastNamedId(initialNamedPresetId());
          }}
        >
          Restablecer
        </Button>
      </div>
    </form>
  );
}
