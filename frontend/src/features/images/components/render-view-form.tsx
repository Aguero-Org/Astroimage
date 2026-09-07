import { type ReactNode, type SyntheticEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  COLORMAP_OPTIONS,
  DEFAULT_RENDER_PARAMS,
  LIMITS_OPTIONS,
  type RenderViewParams,
  STRETCH_OPTIONS,
} from "../render-view";

type RenderViewFormProps = {
  isPending: boolean;
  onSubmit: (params: RenderViewParams) => void;
};

const selectClassName = cn(
  "h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none",
  "focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50",
  "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
);

export function RenderViewForm({
  isPending,
  onSubmit,
}: Readonly<RenderViewFormProps>) {
  const [draft, setDraft] = useState<RenderViewParams>(DEFAULT_RENDER_PARAMS);

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
      <Field
        label="Stretch"
        testId="render-stretch"
        help="Cómo se comprime el brillo de los píxeles. Lineal deja el rango crudo; raíz y log resaltan estructura débil."
      >
        <select
          id="render-stretch"
          data-testid="render-field-stretch"
          className={selectClassName}
          value={draft.stretch}
          disabled={isPending}
          onChange={(event) => {
            setDraft((current) => ({
              ...current,
              stretch: event.target.value,
            }));
          }}
        >
          {STRETCH_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Field
        label="Límites"
        testId="render-limits"
        help="Cómo se elige el rango de intensidad. Percentiles recorta colas; ZScale se adapta al ruido local."
      >
        <select
          id="render-limits"
          data-testid="render-field-limits"
          className={selectClassName}
          value={draft.limits}
          disabled={isPending}
          onChange={(event) => {
            setDraft((current) => ({ ...current, limits: event.target.value }));
          }}
        >
          {LIMITS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Field
        label="Mapa de color"
        testId="render-colormap"
        help="Paleta con la que se pinta el PNG. Gris es el default astronómico; las otras paletas resaltan contraste."
      >
        <select
          id="render-colormap"
          data-testid="render-field-colormap"
          className={selectClassName}
          value={draft.colormap}
          disabled={isPending}
          onChange={(event) => {
            setDraft((current) => ({
              ...current,
              colormap: event.target.value,
            }));
          }}
        >
          {COLORMAP_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
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
              setDraft((current) => ({
                ...current,
                pmin: Number(event.target.value),
              }));
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
              setDraft((current) => ({
                ...current,
                pmax: Number(event.target.value),
              }));
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
            setDraft((current) => ({
              ...current,
              gamma: Number(event.target.value),
            }));
          }}
        />
      </Field>
      <Button
        type="submit"
        data-testid="render-view-submit"
        disabled={isPending}
        className="self-start"
      >
        {isPending ? "Renderizando…" : "Aplicar vista"}
      </Button>
    </form>
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
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex items-center gap-1">
        <label htmlFor={testId} className="text-muted-foreground">
          {label}
        </label>
        <HelpHint
          label={label}
          testId={`render-help-${testId.replace("render-", "")}`}
        >
          {help}
        </HelpHint>
      </div>
      {children}
    </div>
  );
}
