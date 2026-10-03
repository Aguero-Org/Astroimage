import type { ReactNode, SyntheticEvent } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  COLORMAP_OPTIONS,
  DEFAULT_RENDER_PARAMS,
  LIMITS_OPTIONS,
  RENDER_PRESETS,
  type RenderViewParams,
  STRETCH_OPTIONS,
} from "../render-view";
import { useNamedPresetDraft } from "../use-named-preset-draft";
import { DecimalInput } from "./decimal-input";
import { NamedPresetField } from "./named-preset-field";

type RenderNumericKey = "pmin" | "pmax" | "gamma";

type RenderDraft = Omit<RenderViewParams, RenderNumericKey> &
  Record<RenderNumericKey, string>;

function paramsToDraft(params: RenderViewParams): RenderDraft {
  return {
    ...params,
    pmin: String(params.pmin),
    pmax: String(params.pmax),
    gamma: String(params.gamma),
  };
}

function parseRenderDraft(draft: RenderDraft): RenderViewParams | null {
  const pmin = Number(draft.pmin);
  const pmax = Number(draft.pmax);
  const gamma = Number(draft.gamma);
  if (
    !Number.isFinite(pmin) ||
    !Number.isFinite(pmax) ||
    !Number.isFinite(gamma)
  ) {
    return null;
  }
  return {
    stretch: draft.stretch,
    limits: draft.limits,
    colormap: draft.colormap,
    pmin,
    pmax,
    gamma,
  };
}

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
      <Field
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
      </Field>
      <Field
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
      </Field>
      <Field
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
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field
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
        </Field>
        <Field
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
        </Field>
      </div>
      <Field
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
      </Field>
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

const SELECT_THRESHOLD = 5;

type ChoiceOption<T extends string> = { value: T; label: string };

function ExclusiveChoice<T extends string>({
  name,
  value,
  options,
  disabled,
  onChange,
}: Readonly<{
  name: string;
  value: T;
  options: readonly ChoiceOption<T>[];
  disabled: boolean;
  onChange: (value: T) => void;
}>) {
  if (options.length >= SELECT_THRESHOLD) {
    return (
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger
          id={`render-${name}`}
          data-testid={`render-field-${name}`}
          aria-label={name}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem
              key={option.value}
              value={option.value}
              data-testid={`render-field-${name}-${option.value}`}
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  }

  return (
    <div
      role="radiogroup"
      data-testid={`render-field-${name}`}
      className="flex flex-col gap-1"
    >
      {options.map((option) => {
        const optionId = `render-${name}-${option.value}`;
        return (
          <label
            key={option.value}
            htmlFor={optionId}
            className="flex cursor-pointer items-center gap-2 text-sm"
          >
            <input
              id={optionId}
              data-testid={`render-field-${name}-${option.value}`}
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              disabled={disabled}
              onChange={() => {
                onChange(option.value);
              }}
            />
            {option.label}
          </label>
        );
      })}
    </div>
  );
}

function Field({
  label,
  testId,
  help,
  glossaryId,
  children,
}: Readonly<{
  label: string;
  testId: string;
  help: string;
  glossaryId?: string;
  children: ReactNode;
}>) {
  return (
    <fieldset className="flex flex-col gap-1 text-sm">
      <legend className="mb-1 flex items-center gap-1">
        <span className="text-muted-foreground">{label}</span>
        <HelpHint
          label={label}
          testId={`render-help-${testId.replace("render-", "")}`}
          glossaryId={glossaryId}
        >
          {help}
        </HelpHint>
      </legend>
      {children}
    </fieldset>
  );
}
