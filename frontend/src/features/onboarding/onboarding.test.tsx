import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { TooltipRenderProps } from "react-joyride";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { OnboardingLauncher } from "./components/onboarding-launcher";
import { OnboardingTooltip } from "./components/onboarding-tooltip";
import { Onboarding } from "./onboarding";
import { ONBOARDING_STORAGE_KEY, useOnboardingStore } from "./onboarding-store";

const HOME_TARGETS = [
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

const cleanups: Array<() => void> = [];

function mountTargets(testIds: readonly string[]): void {
  for (const testId of testIds) {
    const node = document.createElement("div");
    node.setAttribute("data-testid", testId);
    document.body.append(node);
    cleanups.push(() => node.remove());
  }
}

function startHomeTour(): void {
  mountTargets(HOME_TARGETS);
  useOnboardingStore.getState().start("primeros-pasos");
}

function resetStore(): void {
  useOnboardingStore.setState({ activeTourId: null, completedTourIds: [] });
}

beforeEach(() => {
  localStorage.clear();
  resetStore();
});

afterEach(() => {
  for (const cleanup of cleanups.splice(0)) {
    cleanup();
  }
  resetStore();
});

describe("Onboarding", () => {
  it("renders the active step and advances", async () => {
    const user = userEvent.setup();
    startHomeTour();
    render(<Onboarding />);

    const card = await screen.findByTestId("onboarding-card");
    expect(within(card).getByText("Astroimage")).toBeInTheDocument();
    expect(screen.getByTestId("onboarding-progress")).toHaveTextContent(
      "1 de 10",
    );

    await user.click(screen.getByTestId("onboarding-next"));
    expect(screen.getByTestId("onboarding-progress")).toHaveTextContent(
      "2 de 10",
    );
  });

  it("finishes the tour on the last step", async () => {
    const user = userEvent.setup();
    startHomeTour();
    render(<Onboarding />);
    await screen.findByTestId("onboarding-card");

    for (let step = 0; step < 9; step += 1) {
      await user.click(screen.getByTestId("onboarding-next"));
    }
    expect(screen.getByTestId("onboarding-next")).toHaveTextContent("Listo");

    await user.click(screen.getByTestId("onboarding-next"));

    expect(useOnboardingStore.getState().completedTourIds).toContain(
      "primeros-pasos",
    );
    expect(localStorage.getItem(ONBOARDING_STORAGE_KEY)).toContain(
      "primeros-pasos",
    );
  });

  it("closes without completing when skipped", async () => {
    const user = userEvent.setup();
    startHomeTour();
    render(<Onboarding />);
    await screen.findByTestId("onboarding-card");

    await user.click(screen.getByTestId("onboarding-skip"));

    expect(useOnboardingStore.getState().completedTourIds).toEqual([]);
    expect(screen.queryByTestId("onboarding-card")).not.toBeInTheDocument();
  });

  it("starts the tour automatically when requested", async () => {
    mountTargets(HOME_TARGETS);
    render(<Onboarding autoStartTourId="primeros-pasos" />);
    expect(await screen.findByTestId("onboarding-card")).toBeInTheDocument();
  });

  it("does not start a completed tour automatically", () => {
    useOnboardingStore.setState({ completedTourIds: ["primeros-pasos"] });
    render(<Onboarding autoStartTourId="primeros-pasos" />);
    expect(screen.queryByTestId("onboarding-card")).not.toBeInTheDocument();
  });
});

describe("OnboardingLauncher", () => {
  it("starts the tour from the launcher", async () => {
    const user = userEvent.setup();
    render(
      <TooltipProvider>
        <OnboardingLauncher tourId="primeros-pasos" />
      </TooltipProvider>,
    );

    await user.click(screen.getByTestId("onboarding-launcher"));
    expect(useOnboardingStore.getState().activeTourId).toBe("primeros-pasos");
  });

  it("stays hidden without a tour for the route", () => {
    render(
      <TooltipProvider>
        <OnboardingLauncher />
      </TooltipProvider>,
    );
    expect(screen.queryByTestId("onboarding-launcher")).not.toBeInTheDocument();
  });
});

describe("OnboardingTooltip", () => {
  it("renders progress, title, content and actions", () => {
    const button = (title: string) => ({
      "aria-label": title,
      "data-action": title,
      onClick: () => {},
      role: "button",
      title,
    });
    const props = {
      backProps: button("Atrás"),
      closeProps: button("Cerrar"),
      continuous: true,
      controls: {},
      index: 1,
      isLastStep: false,
      primaryProps: button("Siguiente"),
      size: 4,
      skipProps: button("Omitir"),
      step: { content: "Contenido", title: "Título" },
      tooltipProps: { "aria-modal": true, role: "dialog" },
    } as unknown as TooltipRenderProps;

    render(<OnboardingTooltip {...props} />);

    expect(screen.getByTestId("onboarding-progress")).toHaveTextContent(
      "2 de 4",
    );
    expect(screen.getByText("Título")).toBeInTheDocument();
    expect(screen.getByText("Contenido")).toBeInTheDocument();
    expect(screen.getByTestId("onboarding-previous")).toHaveTextContent(
      "Atrás",
    );
    expect(screen.getByTestId("onboarding-next")).toHaveTextContent(
      "Siguiente",
    );
  });
});
