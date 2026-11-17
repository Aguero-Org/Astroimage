import { useEffect, useMemo } from "react";
import { type EventData, Joyride, type Options } from "react-joyride";
import { OnboardingTooltip } from "./components/onboarding-tooltip";
import { useOnboardingStore } from "./onboarding-store";
import { buildSteps, getTour } from "./tours";

const LOCALE = {
  back: "Atrás",
  next: "Siguiente",
  last: "Listo",
  skip: "Omitir",
  close: "Cerrar",
};

const OPTIONS: Partial<Options> = {
  skipBeacon: true,
  primaryColor: "var(--primary)",
  backgroundColor: "var(--popover)",
  textColor: "var(--popover-foreground)",
  arrowColor: "var(--popover)",
  overlayColor: "color-mix(in srgb, var(--palette-5) 55%, transparent)",
  spotlightRadius: 8,
  spotlightPadding: 6,
  zIndex: 60,
  targetWaitTimeout: 3000,
  closeButtonAction: "skip",
};

type OnboardingProps = {
  autoStartTourId?: string;
};

export function Onboarding({
  autoStartTourId,
}: Readonly<OnboardingProps> = {}) {
  const activeTourId = useOnboardingStore((state) => state.activeTourId);
  const completedTourIds = useOnboardingStore(
    (state) => state.completedTourIds,
  );
  const start = useOnboardingStore((state) => state.start);
  const finish = useOnboardingStore((state) => state.finish);
  const dismiss = useOnboardingStore((state) => state.dismiss);

  useEffect(() => {
    if (!autoStartTourId || activeTourId) {
      return;
    }
    if (completedTourIds.includes(autoStartTourId)) {
      return;
    }
    if (!getTour(autoStartTourId)) {
      return;
    }
    start(autoStartTourId);
  }, [autoStartTourId, activeTourId, completedTourIds, start]);

  const tour = activeTourId ? getTour(activeTourId) : undefined;
  const steps = useMemo(
    () =>
      tour ? buildSteps(tour).map((step) => ({ ...step, isFixed: true })) : [],
    [tour],
  );

  if (!tour) {
    return null;
  }

  const handleEvent = (data: EventData) => {
    if (data.type !== "tour:end") {
      return;
    }
    if (data.status === "finished") {
      finish();
    } else if (data.status === "skipped") {
      dismiss();
    }
  };

  return (
    <Joyride
      steps={steps}
      run
      continuous
      scrollToFirstStep
      options={OPTIONS}
      locale={LOCALE}
      tooltipComponent={OnboardingTooltip}
      onEvent={handleEvent}
    />
  );
}
