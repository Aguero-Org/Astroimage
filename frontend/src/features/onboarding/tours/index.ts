import type { Step } from "react-joyride";
import { glosario } from "./glosario";
import { primerosPasos } from "./primeros-pasos";
import type { OnboardingStep, OnboardingTour } from "./types";
import { visor } from "./visor";

export type { OnboardingStep, OnboardingTour };

export const TOURS: readonly OnboardingTour[] = [
  primerosPasos,
  visor,
  glosario,
];

function withoutRequires(step: OnboardingStep): Step {
  const clone: Record<string, unknown> = { ...step };
  delete clone.requires;
  return clone as Step;
}

export function buildSteps(
  tour: OnboardingTour,
  root: ParentNode = document,
): Step[] {
  return tour.steps
    .filter((step) => !step.requires || root.querySelector(step.requires))
    .map(withoutRequires);
}

export function matchesRoute(pathname: string, route: string): boolean {
  if (route === "/") {
    return pathname === "/";
  }
  return pathname === route || pathname.startsWith(`${route}/`);
}

export function getTour(tourId: string): OnboardingTour | undefined {
  return TOURS.find((tour) => tour.id === tourId);
}

export function tourForRoute(pathname: string): OnboardingTour | undefined {
  return TOURS.find((tour) => matchesRoute(pathname, tour.route));
}
