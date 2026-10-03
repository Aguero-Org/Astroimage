import { Input } from "@/components/ui/input";

type DecimalInputProps = {
  id: string;
  testId: string;
  value: string;
  disabled?: boolean;
  step?: string;
  onValueChange: (value: string) => void;
};

export function DecimalInput({
  id,
  testId,
  value,
  disabled,
  step,
  onValueChange,
}: Readonly<DecimalInputProps>) {
  return (
    <Input
      id={id}
      data-testid={testId}
      type="text"
      inputMode="decimal"
      autoComplete="off"
      spellCheck={false}
      step={step}
      value={value}
      disabled={disabled}
      onChange={(event) => {
        onValueChange(event.target.value);
      }}
    />
  );
}
