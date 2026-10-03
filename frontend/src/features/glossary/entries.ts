import { FUENTES_ENTRIES } from "./entries-fuentes";
import { IMAGEN_ENTRIES } from "./entries-imagen";
import { VISOR_ENTRIES } from "./entries-visor";
import { VISTA_ENTRIES } from "./entries-vista";
import type { GlossaryEntry } from "./glossary-types";

export {
  GLOSSARY_GROUPS,
  type GlossaryEntry,
  type GlossaryGroupId,
} from "./glossary-types";

export const GLOSSARY_ENTRIES: GlossaryEntry[] = [
  ...IMAGEN_ENTRIES,
  ...VISTA_ENTRIES,
  ...FUENTES_ENTRIES,
  ...VISOR_ENTRIES,
];

export function filterGlossaryEntries(
  entries: readonly GlossaryEntry[],
  query: string,
): GlossaryEntry[] {
  const needle = query.trim().toLowerCase();
  if (needle.length === 0) {
    return [...entries];
  }
  return entries.filter((entry) => {
    const haystack = `${entry.name} ${entry.what} ${entry.inApp} ${entry.where}`;
    return haystack.toLowerCase().includes(needle);
  });
}

export function glossaryPath(id: string): string {
  return `/glossary#${id}`;
}
