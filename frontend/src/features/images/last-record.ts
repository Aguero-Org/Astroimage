export const LAST_IMAGE_RECORD_KEY = "astroimage-last-record";

export type LastImageRecord = {
  recordId: string;
  slug?: string;
};

const listeners = new Set<() => void>();
let cachedRaw: string | null = null;
let cachedRecord: LastImageRecord | null = null;

export function rememberLastImageRecord(recordId: string, slug?: string): void {
  const value: LastImageRecord = slug ? { recordId, slug } : { recordId };
  sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, JSON.stringify(value));
  for (const listener of listeners) {
    listener();
  }
}

export function subscribeLastImageRecord(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function parseLastImageRecord(raw: string | null): LastImageRecord | null {
  if (!raw) {
    return null;
  }
  if (!raw.startsWith("{")) {
    return { recordId: raw };
  }
  try {
    const parsed = JSON.parse(raw) as LastImageRecord;
    if (typeof parsed.recordId !== "string" || parsed.recordId === "") {
      return null;
    }
    return parsed.slug ? parsed : { recordId: parsed.recordId };
  } catch {
    return null;
  }
}

export function readLastImageRecord(): LastImageRecord | null {
  const raw = sessionStorage.getItem(LAST_IMAGE_RECORD_KEY);
  if (raw === cachedRaw) {
    return cachedRecord;
  }
  cachedRaw = raw;
  cachedRecord = parseLastImageRecord(raw);
  return cachedRecord;
}
