export const CUSTOM_PRESET_ID = "custom";

export type NamedPreset<T> = {
  id: string;
  label: string;
  outcome: string;
  hint: string;
  values: T;
};

export function matchNamedPreset<T>(
  presets: readonly NamedPreset<T>[],
  values: T,
): string {
  const found = presets.find((preset) =>
    shallowEqualRecord(
      preset.values as Record<string, unknown>,
      values as Record<string, unknown>,
    ),
  );
  return found?.id ?? CUSTOM_PRESET_ID;
}

function shallowEqualRecord(
  left: Record<string, unknown>,
  right: Record<string, unknown>,
): boolean {
  const keys = Object.keys(left);
  if (keys.length !== Object.keys(right).length) {
    return false;
  }
  return keys.every((key) => Object.is(left[key], right[key]));
}
