import { HelpHint } from "@/components/ui/help-hint";
import { Label } from "@/components/ui/label";
import type { DetectionField } from "../source-detection-fields";
import { DecimalInput } from "./decimal-input";

export function DetectionFieldInput({
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
        <Label
          htmlFor={field.key}
          className="font-normal leading-normal text-muted-foreground"
        >
          {field.label}
        </Label>
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
