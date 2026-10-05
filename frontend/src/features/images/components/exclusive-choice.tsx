import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const SELECT_THRESHOLD = 5;

type ChoiceOption<T extends string> = { value: T; label: string };

export function ExclusiveChoice<T extends string>({
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
