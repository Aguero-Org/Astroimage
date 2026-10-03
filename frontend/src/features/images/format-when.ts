const MJD_EPOCH_MS = Date.UTC(1858, 10, 17);

export function formatWhen(value: string | null): string {
  if (value === null || value === "") {
    return "—";
  }
  if (/^\d+(\.\d+)?$/.test(value)) {
    const modifiedJulianDay = Number(value);
    if (modifiedJulianDay > 30000 && modifiedJulianDay < 90000) {
      return new Date(
        MJD_EPOCH_MS + modifiedJulianDay * 86_400_000,
      ).toLocaleString();
    }
  }
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return value;
  }
  return new Date(parsed).toLocaleDateString();
}
