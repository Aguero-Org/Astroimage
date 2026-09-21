export const LAST_IMAGE_RECORD_KEY = "astroimage-last-record";

export function rememberLastImageRecord(recordId: string): void {
  sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, recordId);
}

export function readLastImageRecord(): string | null {
  return sessionStorage.getItem(LAST_IMAGE_RECORD_KEY);
}
