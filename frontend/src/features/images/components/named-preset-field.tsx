import { useState } from "react";
import { HelpHint } from "@/components/ui/help-hint";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CUSTOM_PRESET_ID, type NamedPreset } from "../named-preset";

const CUSTOM_OUTCOME =
  "Los campos quedan como los dejaste; no es un preset guardado.";

type NamedPresetFieldProps<T> = {
  label: string;
  testId: string;
  glossaryId?: string;
  presets: readonly NamedPreset<T>[];
  value: string;
  lastNamedId: string;
  disabled: boolean;
  onSelect: (preset: NamedPreset<T>) => void;
};

export function NamedPresetField<T>({
  label,
  testId,
  glossaryId,
  presets,
  value,
  lastNamedId,
  disabled,
  onSelect,
}: Readonly<NamedPresetFieldProps<T>>) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const selected =
    presets.find((preset) => preset.id === value) ??
    presets.find((preset) => preset.id === lastNamedId);
  const triggerLabel =
    value === CUSTOM_PRESET_ID
      ? "Personalizado"
      : (selected?.label ?? "Personalizado");
  const hoveredPreset = presets.find((preset) => preset.id === hoveredId);
  const outcome =
    hoveredId === CUSTOM_PRESET_ID
      ? CUSTOM_OUTCOME
      : (hoveredPreset?.outcome ?? selected?.outcome);
  const hint = selected?.hint;

  return (
    <fieldset className="flex flex-col gap-1 text-sm">
      <legend className="mb-1 flex items-center gap-1">
        <span className="text-muted-foreground">{label}</span>
        {hint ? (
          <HelpHint
            label={label}
            testId={`${testId}-help`}
            glossaryId={glossaryId}
          >
            {hint}
          </HelpHint>
        ) : null}
      </legend>
      <Select
        value={value}
        disabled={disabled}
        onValueChange={(nextId) => {
          setHoveredId(null);
          const preset = presets.find((item) => item.id === nextId);
          if (preset) {
            onSelect(preset);
          }
        }}
        onOpenChange={(open) => {
          if (!open) {
            setHoveredId(null);
          }
        }}
      >
        <SelectTrigger id={testId} data-testid={testId} aria-label={label}>
          <SelectValue>{triggerLabel}</SelectValue>
        </SelectTrigger>
        <SelectContent
          onPointerLeave={() => {
            setHoveredId(null);
          }}
          footer={
            outcome ? (
              <p
                data-testid={`${testId}-hover-hint`}
                className="border-t border-border bg-popover px-3 py-2 text-xs leading-snug text-muted-foreground"
              >
                {outcome}
              </p>
            ) : null
          }
        >
          <SelectItem
            value={CUSTOM_PRESET_ID}
            data-testid={`${testId}-custom`}
            onPointerEnter={() => {
              setHoveredId(CUSTOM_PRESET_ID);
            }}
            onFocus={() => {
              setHoveredId(CUSTOM_PRESET_ID);
            }}
          >
            Personalizado
          </SelectItem>
          {presets.map((preset) => (
            <SelectItem
              key={preset.id}
              value={preset.id}
              data-testid={`${testId}-${preset.id}`}
              onPointerEnter={() => {
                setHoveredId(preset.id);
              }}
              onFocus={() => {
                setHoveredId(preset.id);
              }}
            >
              {preset.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selected || value === CUSTOM_PRESET_ID ? (
        <p
          data-testid={`${testId}-outcome`}
          className="min-h-8 text-muted-foreground text-xs leading-snug"
        >
          {selected?.outcome ?? CUSTOM_OUTCOME}
        </p>
      ) : null}
    </fieldset>
  );
}
