export function orUnavailable(value: string | null | undefined): string {
  if (
    value === null ||
    value === undefined ||
    value.trim() === "" ||
    value === "—" ||
    value === "--" ||
    value === "-"
  ) {
    return "No disponible";
  }
  return value;
}
