import { type ReactNode, type SyntheticEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CUSTOM_PRESET_ID, matchNamedPreset } from "../named-preset";
import {
  COLORMAP_OPTIONS,
  DEFAULT_RENDER_PARAMS,
  LIMITS_OPTIONS,
  RENDER_PRESETS,
  type RenderViewParams,
  STRETCH_OPTIONS,
} from "../render-view";
import { NamedPresetField } from "./named-preset-field";

type RenderViewFormProps = {
  isPending: boolean;
  onSubmit: (params: RenderViewParams) => void;
};

export function RenderViewForm({
  isPending,
  onSubmit,
}: Readonly<RenderViewFormProps>) {
  const [draft, setDraft] = useState<RenderViewParams>(DEFAULT_RENDER_PARAMS);
  const [presetId, setPresetId] = useState(() =>
    matchNamedPreset(RENDER_PRESETS, DEFAULT_RENDER_PARAMS),
  );
  const [lastNamedId, setLastNamedId] = useState("estandar");

  function applyDraft(next: RenderViewParams) {
    setDraft(next);
    const matched = matchNamedPreset(RENDER_PRESETS, next);
    setPresetId(matched);
    if (matched !== CUSTOM_PRESET_ID) {
      setLastNamedId(matched);
    }
  }

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !Number.isFinite(draft.pmin) ||
      !Number.isFinite(draft.pmax) ||
      !Number.isFinite(draft.gamma) ||
      draft.pmin >= draft.pmax
    ) {
      return;
    }
    onSubmit(draft);
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
        presets={RENDER_PRESETS}
        value={presetId}
        lastNamedId={lastNamedId}
        disabled={isPending}
        onSelect={(preset) => {
          applyDraft(preset.values);
        }}
      />
      <Field
        label="Stretch"
        testId="render-stretch"
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
          help="Percentil inferior del recorte (0–100). Subirlo oculta fondo; debe ser menor que Pmax."
        >
          <Input
            id="render-pmin"
            data-testid="render-field-pmin"
            type="number"
            step="0.1"
            min={0}
            max={99.9}
            value={draft.pmin}
            disabled={isPending}
            onChange={(event) => {
              applyDraft({
                ...draft,
                pmin: Number(event.target.value),
              });
            }}
          />
        </Field>
        <Field
          label="Pmax"
          testId="render-pmax"
          help="Percentil superior del recorte (0–100). Bajarlo satura menos las estrellas brillantes."
        >
          <Input
            id="render-pmax"
            data-testid="render-field-pmax"
            type="number"
            step="0.1"
            min={0.1}
            max={100}
            value={draft.pmax}
            disabled={isPending}
            onChange={(event) => {
              applyDraft({
                ...draft,
                pmax: Number(event.target.value),
              });
            }}
          />
        </Field>
      </div>
      <Field
        label="Gamma"
        testId="render-gamma"
        help="Curva extra sobre el stretch (0.1–5). Menor que 1 aclara medios tonos; mayor que 1 los oscurece."
      >
        <Input
          id="render-gamma"
          data-testid="render-field-gamma"
          type="number"
          step="0.1"
          min={0.1}
          max={5}
          value={draft.gamma}
          disabled={isPending}
          onChange={(event) => {
            applyDraft({
              ...draft,
              gamma: Number(event.target.value),
            });
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
            applyDraft(DEFAULT_RENDER_PARAMS);
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
  children,
}: Readonly<{
  label: string;
  testId: string;
  help: string;
  children: ReactNode;
}>) {
  return (
    <fieldset className="flex flex-col gap-1 text-sm">
      <legend className="mb-1 flex items-center gap-1">
        <span className="text-muted-foreground">{label}</span>
        <HelpHint
          label={label}
          testId={`render-help-${testId.replace("render-", "")}`}
        >
          {help}
        </HelpHint>
      </legend>
      {children}
    </fieldset>
  );
}
