import { create } from "zustand";
import {
  createJSONStorage,
  persist,
  type StateStorage,
} from "zustand/middleware";

export const LAST_IMAGE_RECORD_KEY = "astroimage-last-record";

export type LastImageRecord = {
  recordId: string;
  slug?: string;
};

type LastRecordState = {
  record: LastImageRecord | null;
  remember: (recordId: string, slug?: string) => void;
  clear: () => void;
};

function normalizeRecord(value: unknown): LastImageRecord | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const recordId = (value as { recordId?: unknown }).recordId;
  if (typeof recordId !== "string" || recordId === "") {
    return null;
  }
  const slug = (value as { slug?: unknown }).slug;
  return typeof slug === "string" && slug !== ""
    ? { recordId, slug }
    : { recordId };
}

function parseLastImageRecord(raw: string | null): LastImageRecord | null {
  if (!raw) {
    return null;
  }
  if (!raw.startsWith("{")) {
    return { recordId: raw };
  }
  try {
    return normalizeRecord(JSON.parse(raw));
  } catch {
    return null;
  }
}

function toEnvelope(raw: string | null): string | null {
  if (raw === null) {
    return null;
  }
  return JSON.stringify({
    state: { record: parseLastImageRecord(raw) },
    version: 0,
  });
}

function envelopeRecord(value: string): LastImageRecord | null {
  try {
    const parsed = JSON.parse(value) as {
      state?: { record?: unknown };
    };
    return normalizeRecord(parsed.state?.record);
  } catch {
    return null;
  }
}

const rawSessionStorage: StateStorage = {
  getItem: (name) => {
    if (typeof sessionStorage === "undefined") {
      return null;
    }
    return toEnvelope(sessionStorage.getItem(name));
  },
  setItem: (name, value) => {
    if (typeof sessionStorage === "undefined") {
      return;
    }
    const record = envelopeRecord(value);
    if (record === null) {
      sessionStorage.removeItem(name);
      return;
    }
    sessionStorage.setItem(name, JSON.stringify(record));
  },
  removeItem: (name) => {
    if (typeof sessionStorage === "undefined") {
      return;
    }
    sessionStorage.removeItem(name);
  },
};

export const useLastRecordStore = create<LastRecordState>()(
  persist(
    (set) => ({
      record: null,
      remember: (recordId, slug) => {
        set({ record: slug ? { recordId, slug } : { recordId } });
      },
      clear: () => {
        set({ record: null });
      },
    }),
    {
      name: LAST_IMAGE_RECORD_KEY,
      storage: createJSONStorage(() => rawSessionStorage),
      partialize: (state) => ({ record: state.record }),
    },
  ),
);

export function rememberLastImageRecord(recordId: string, slug?: string): void {
  useLastRecordStore.getState().remember(recordId, slug);
}
