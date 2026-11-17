import type { Step } from "react-joyride";

export type OnboardingStep = Step & {
  /** Only show the step when this selector matches an element. */
  readonly requires?: string;
};

export type OnboardingTour = {
  readonly id: string;
  readonly route: string;
  readonly label: string;
  readonly steps: readonly OnboardingStep[];
};
