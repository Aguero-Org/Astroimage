import { describe, expect, it } from "vitest";
import { buildSteps, getTour, matchesRoute, tourForRoute } from "./tours";

function rootWith(testIds: readonly string[]): HTMLElement {
  const root = document.createElement("div");
  for (const testId of testIds) {
    const element = document.createElement("span");
    element.setAttribute("data-testid", testId);
    root.append(element);
  }
  return root;
}

describe("matchesRoute", () => {
  it("matches the home route exactly", () => {
    expect(matchesRoute("/", "/")).toBe(true);
    expect(matchesRoute("/image/m31", "/")).toBe(false);
  });

  it("matches a route and its children", () => {
    expect(matchesRoute("/image", "/image")).toBe(true);
    expect(matchesRoute("/image/m31", "/image")).toBe(true);
    expect(matchesRoute("/image/m31/andromeda", "/image")).toBe(true);
  });

  it("does not match a sibling prefix", () => {
    expect(matchesRoute("/images", "/image")).toBe(false);
  });
});

describe("tourForRoute", () => {
  it("returns the home tour for the home route", () => {
    expect(tourForRoute("/")?.id).toBe("primeros-pasos");
  });

  it("returns the viewer tour for an image route", () => {
    expect(tourForRoute("/image/m31")?.id).toBe("visor");
    expect(tourForRoute("/image/m31/andromeda")?.id).toBe("visor");
  });

  it("returns the glossary tour for the glossary route", () => {
    expect(tourForRoute("/glossary")?.id).toBe("glosario");
  });

  it("returns undefined for a route without a tour", () => {
    expect(tourForRoute("/desconocido")).toBeUndefined();
  });
});

describe("getTour", () => {
  it("finds a tour by id", () => {
    expect(getTour("visor")?.route).toBe("/image");
  });

  it("returns undefined for an unknown id", () => {
    expect(getTour("nope")).toBeUndefined();
  });
});

describe("buildSteps", () => {
  it("drops steps whose required target is absent", () => {
    const tour = getTour("visor");
    if (!tour) {
      throw new Error("visor tour missing");
    }
    const steps = buildSteps(tour, rootWith([]));
    expect(steps).toHaveLength(11);
    expect(steps.every((step) => !("requires" in step))).toBe(true);
  });

  it("keeps a step when its required target exists", () => {
    const tour = getTour("visor");
    if (!tour) {
      throw new Error("visor tour missing");
    }
    const root = document.createElement("div");
    const marker = document.createElement("span");
    marker.setAttribute("data-testid", "source-marker");
    marker.setAttribute("data-gaia-match", "true");
    root.append(marker);
    expect(buildSteps(tour, root)).toHaveLength(12);
  });

  it("keeps every home step when all targets exist", () => {
    const tour = getTour("primeros-pasos");
    if (!tour) {
      throw new Error("home tour missing");
    }
    const all = [
      "home-title",
      "search-input",
      "image-list",
      "image-list-item-open",
      "edit-image",
      "download-stored-fits",
      "delete-image",
      "import-fits",
      "home-glossary",
      "theme-toggle",
    ];
    expect(buildSteps(tour, rootWith(all))).toHaveLength(10);
  });
});
