import { create } from "zustand";
import { persist } from "zustand/middleware";

export const ONBOARDING_STORAGE_KEY = "astroimage-onboarding-completed";

export function sanitizeCompleted(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((id): id is string => typeof id === "string")
    : [];
}

type OnboardingState = {
  activeTourId: string | null;
  completedTourIds: string[];
  start: (tourId: string) => void;
  finish: () => void;
  dismiss: () => void;
  reset: () => void;
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set, get) => ({
      activeTourId: null,
      completedTourIds: [],
      start: (tourId) => set({ activeTourId: tourId }),
      finish: () => {
        const { activeTourId, completedTourIds } = get();
        const next =
          activeTourId && !completedTourIds.includes(activeTourId)
            ? [...completedTourIds, activeTourId]
            : completedTourIds;
        set({ activeTourId: null, completedTourIds: next });
      },
      dismiss: () => set({ activeTourId: null }),
      reset: () => set({ activeTourId: null, completedTourIds: [] }),
    }),
    {
      name: ONBOARDING_STORAGE_KEY,
      partialize: (state) => ({ completedTourIds: state.completedTourIds }),
      merge: (persisted, current) => ({
        ...current,
        completedTourIds: sanitizeCompleted(
          (persisted as { completedTourIds?: unknown } | undefined)
            ?.completedTourIds,
        ),
      }),
    },
  ),
);
