import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { glossaryPath } from "@/features/glossary/entries";
import { DEFAULT_CROSSMATCH_PARAMS } from "../crossmatch";
import { CrossmatchSettingsForm } from "./crossmatch-settings-form";

function renderForm(onSubmit = vi.fn()) {
  render(
    <TooltipProvider delayDuration={0}>
      <CrossmatchSettingsForm
        params={DEFAULT_CROSSMATCH_PARAMS}
        onSubmit={onSubmit}
      />
    </TooltipProvider>,
  );
  return onSubmit;
}

describe("CrossmatchSettingsForm", () => {
  it("shows the current radius and probability power", () => {
    renderForm();

    expect(screen.getByTestId("crossmatch-gaia-radius")).toHaveValue("5");
    expect(screen.getByTestId("crossmatch-gaia-power")).toHaveValue("2");
    expect(screen.getByTestId("crossmatch-simbad-radius")).toHaveValue("5");
    expect(screen.getByTestId("crossmatch-simbad-power")).toHaveValue("2");
    expect(screen.getAllByText("Radio de cruce")).toHaveLength(2);
    expect(screen.getAllByText("Exponente de probabilidad")).toHaveLength(2);
    expect(screen.getAllByLabelText("Radio de cruce")).toHaveLength(2);
    expect(screen.getAllByLabelText("Exponente de probabilidad")).toHaveLength(
      2,
    );
    expect(screen.getByTestId("crossmatch-gaia-radius")).toHaveAttribute(
      "step",
      "0.5",
    );
    expect(screen.getByTestId("crossmatch-gaia-power")).toHaveAttribute(
      "step",
      "0.1",
    );
    expect(screen.getByTestId("crossmatch-simbad-radius")).toHaveAttribute(
      "step",
      "0.5",
    );
    expect(screen.getByTestId("crossmatch-simbad-power")).toHaveAttribute(
      "step",
      "0.1",
    );
    expect(
      screen.getByTestId("crossmatch-help-crossmatch-gaia-radius"),
    ).toHaveAccessibleName("Ayuda: Radio de cruce");
    expect(
      screen.getByTestId("crossmatch-help-crossmatch-gaia-radius-glossary"),
    ).toHaveAttribute("href", glossaryPath("radio-cruce"));
    expect(
      screen.getByTestId("crossmatch-help-crossmatch-gaia-power-glossary"),
    ).toHaveAttribute("href", glossaryPath("exponente-probabilidad"));
    expect(
      screen.getByTestId("crossmatch-help-crossmatch-simbad-radius-glossary"),
    ).toHaveAttribute("href", glossaryPath("radio-cruce"));
    expect(
      screen.getByTestId("crossmatch-help-crossmatch-simbad-power-glossary"),
    ).toHaveAttribute("href", glossaryPath("exponente-probabilidad"));
    expect(screen.getByTestId("crossmatch-help-glossary")).toHaveAttribute(
      "href",
      glossaryPath("radio-cruce"),
    );
    expect(screen.queryByTestId("crossmatch-error")).not.toBeInTheDocument();
  });

  it.each([
    ["crossmatch-help", /Definen qué separación/],
    ["crossmatch-help-crossmatch-gaia-radius", /una fuente Gaia/],
    ["crossmatch-help-crossmatch-gaia-power", /la fuente se aleja/],
    ["crossmatch-help-crossmatch-simbad-radius", /un objeto SIMBAD/],
    ["crossmatch-help-crossmatch-simbad-power", /el objeto se aleja/],
  ])("explains %s in its help tooltip", async (testId, text) => {
    const user = userEvent.setup();
    renderForm();

    await user.hover(screen.getByTestId(testId));
    expect(await screen.findByText(text)).toBeInTheDocument();
  });

  it("prevents the native submit and applies valid defaults", () => {
    const onSubmit = renderForm();

    const notPrevented = fireEvent.submit(
      screen.getByTestId("crossmatch-settings-form"),
    );

    expect(notPrevented).toBe(false);
    expect(onSubmit).toHaveBeenCalledWith(DEFAULT_CROSSMATCH_PARAMS);
  });

  it("submits the edited values for both catalogs", async () => {
    const user = userEvent.setup();
    const onSubmit = renderForm();

    await replace(user, "crossmatch-gaia-radius", "6.5");
    await replace(user, "crossmatch-gaia-power", "1.5");
    await replace(user, "crossmatch-simbad-radius", "4");
    await replace(user, "crossmatch-simbad-power", "3");
    await user.click(screen.getByTestId("crossmatch-apply"));

    expect(onSubmit).toHaveBeenCalledWith({
      gaiaRadiusArcsec: 6.5,
      gaiaProbabilityPower: 1.5,
      simbadRadiusArcsec: 4,
      simbadProbabilityPower: 3,
    });
  });

  it("blocks the submit when a value is out of range", async () => {
    const user = userEvent.setup();
    const onSubmit = renderForm();

    await replace(user, "crossmatch-gaia-radius", "3601");

    expect(screen.getByTestId("crossmatch-apply")).toBeDisabled();
    expect(screen.getByTestId("crossmatch-error")).toBeInTheDocument();

    fireEvent.submit(screen.getByTestId("crossmatch-settings-form"));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

async function replace(
  user: ReturnType<typeof userEvent.setup>,
  testId: string,
  value: string,
) {
  const input = screen.getByTestId(testId);
  await user.clear(input);
  await user.type(input, value);
}
