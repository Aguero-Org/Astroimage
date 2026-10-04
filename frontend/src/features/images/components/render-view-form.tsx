import type { SyntheticEvent } from "react";
import { Button } from "@/components/ui/button";
import {
  COLORMAP_OPTIONS,
  DEFAULT_RENDER_PARAMS,
  LIMITS_OPTIONS,
  paramsToDraft,
  parseRenderDraft,
  RENDER_PRESETS,
  type RenderViewParams,
  STRETCH_OPTIONS,
} from "../render-view";
import { useNamedPresetDraft } from "../use-named-preset-draft";
import { DecimalInput } from "./decimal-input";
import { ExclusiveChoice } from "./exclusive-choice";
import { NamedPresetField } from "./named-preset-field";
import { RenderField } from "./render-field";

type RenderViewFormProps = {
  isPending: boolean;
  onSubmit: (params: RenderViewParams) => void;
};

export function RenderViewForm({
  isPending,
  onSubmit,
}: Readonly<RenderViewFormProps>) {
  const { draft, presetId, lastNamedId, applyParams, applyDraft, parseDraft } =
    useNamedPresetDraft({
      presets: RENDER_PRESETS,
      defaults: DEFAULT_RENDER_PARAMS,
      toDraft: paramsToDraft,
      parseDraft: parseRenderDraft,
    });

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = parseDraft();
    if (parsed === null || parsed.pmin >= parsed.pmax) {
      return;
    }
    onSubmit(parsed);
  }

  return (
    <form
      data-testid="render-view-form"
      className="flex flex-col gap-3"
      onSubmit={handleSubmit}
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
          applyParams(preset.values);
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
            applyDraft({ ...draft, stretch });
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
            applyDraft({ ...draft, limits });
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
            applyDraft({ ...draft, colormap });
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
              applyDraft({ ...draft, pmin });
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
              applyDraft({ ...draft, pmax });
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
            applyDraft({ ...draft, gamma });
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
            applyParams(DEFAULT_RENDER_PARAMS);
          }}
        >
          Restablecer
        </Button>
      </div>
    </form>
  );
}
