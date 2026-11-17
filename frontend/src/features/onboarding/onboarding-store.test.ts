import { beforeEach, describe, expect, it } from "vitest";
import {
  ONBOARDING_STORAGE_KEY,
  sanitizeCompleted,
  useOnboardingStore,
} from "./onboarding-store";

function resetStore(): void {
  useOnboardingStore.setState({ activeTourId: null, completedTourIds: [] });
}

function persisted(): { completedTourIds?: string[] } {
  const raw = localStorage.getItem(ONBOARDING_STORAGE_KEY);
  return raw ? (JSON.parse(raw).state ?? {}) : {};
}

beforeEach(() => {
  localStorage.clear();
  resetStore();
});

describe("sanitizeCompleted", () => {
  it("keeps only string entries", () => {
    expect(sanitizeCompleted(["a", 1, "b", null])).toEqual(["a", "b"]);
  });

  it("returns an empty list for a non-array value", () => {
    expect(sanitizeCompleted("nope")).toEqual([]);
    expect(sanitizeCompleted(undefined)).toEqual([]);
  });
});

describe("useOnboardingStore", () => {
  it("starts a tour", () => {
    useOnboardingStore.getState().start("primeros-pasos");
    expect(useOnboardingStore.getState().activeTourId).toBe("primeros-pasos");
  });

  it("marks the tour completed and persists it on finish", () => {
    useOnboardingStore.getState().start("primeros-pasos");
    useOnboardingStore.getState().finish();

    expect(useOnboardingStore.getState().activeTourId).toBeNull();
    expect(useOnboardingStore.getState().completedTourIds).toEqual([
      "primeros-pasos",
    ]);
    expect(persisted().completedTourIds).toEqual(["primeros-pasos"]);
  });

  it("does not duplicate a completed tour", () => {
    useOnboardingStore.setState({ completedTourIds: ["primeros-pasos"] });
    useOnboardingStore.getState().start("primeros-pasos");
    useOnboardingStore.getState().finish();
    expect(useOnboardingStore.getState().completedTourIds).toEqual([
      "primeros-pasos",
    ]);
  });

  it("closes without marking on dismiss", () => {
    useOnboardingStore.getState().start("primeros-pasos");
    useOnboardingStore.getState().dismiss();

    expect(useOnboardingStore.getState().activeTourId).toBeNull();
    expect(useOnboardingStore.getState().completedTourIds).toEqual([]);
    expect(persisted().completedTourIds).toEqual([]);
  });

  it("clears the stored completion on reset", () => {
    useOnboardingStore.setState({ completedTourIds: ["primeros-pasos"] });
    useOnboardingStore.getState().reset();

    expect(useOnboardingStore.getState().completedTourIds).toEqual([]);
    expect(persisted().completedTourIds).toEqual([]);
  });
});
