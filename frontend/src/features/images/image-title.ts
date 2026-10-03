const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function isTechnicalName(value: string): boolean {
  return UUID.test(value) || /\.fits?$/i.test(value);
}

export function humanizeImageSlug(slug: string): string {
  const withoutHash = slug.replace(/-[0-9a-f]{6,12}$/i, "");
  return withoutHash
    .split("-")
    .filter((part) => part.length > 0)
    .map((part) => part.toUpperCase())
    .join(" ");
}

export function imageDisplayTitle(
  sourceName: string | null | undefined,
  slug: string | undefined,
): string {
  const trimmed = sourceName?.trim() ?? "";
  if (trimmed.length > 0 && !isTechnicalName(trimmed)) {
    return trimmed;
  }
  if (slug && slug.trim().length > 0) {
    const friendly = humanizeImageSlug(slug);
    if (friendly.length > 0) {
      return friendly;
    }
  }
  if (trimmed.length > 0) {
    return trimmed.replace(/\.fits?$/i, "");
  }
  return "Imagen";
}
