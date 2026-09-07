import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { DEFAULT_RENDER_PARAMS } from "../render-view";
import { RenderViewForm } from "./render-view-form";

function renderForm(onSubmit = vi.fn()) {
  return {
    onSubmit,
    user: userEvent.setup(),
    ...render(
      <TooltipProvider delayDuration={0}>
        <RenderViewForm isPending={false} onSubmit={onSubmit} />
      </TooltipProvider>,
    ),
  };
}

describe("RenderViewForm", () => {
  it("submits backend default render parameters", async () => {
    const { onSubmit, user } = renderForm();

    await user.click(screen.getByTestId("render-view-submit"));
    expect(onSubmit).toHaveBeenCalledWith(DEFAULT_RENDER_PARAMS);
  });

  it("uses radios for stretch and a select for colormap", () => {
    renderForm();

    expect(screen.getByTestId("render-field-stretch-sqrt")).toHaveAttribute(
      "type",
      "radio",
    );
    expect(
      screen.getByTestId("render-field-limits-percentiles"),
    ).toHaveAttribute("type", "radio");
    expect(screen.getByTestId("render-field-colormap").tagName).toBe("SELECT");
  });

  it("submits a changed stretch from the radio group", async () => {
    const { onSubmit, user } = renderForm();

    await user.click(screen.getByTestId("render-field-stretch-log"));
    await user.click(screen.getByTestId("render-view-submit"));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ stretch: "log" }),
    );
  });

  it("submits a changed colormap", async () => {
    const { onSubmit, user } = renderForm();

    await user.selectOptions(
      screen.getByTestId("render-field-colormap"),
      "heat",
    );
    await user.click(screen.getByTestId("render-view-submit"));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ colormap: "heat" }),
    );
  });

  it("does not submit when pmin is not lower than pmax", async () => {
    const { onSubmit, user } = renderForm();

    await user.clear(screen.getByTestId("render-field-pmin"));
    await user.type(screen.getByTestId("render-field-pmin"), "99");
    await user.clear(screen.getByTestId("render-field-pmax"));
    await user.type(screen.getByTestId("render-field-pmax"), "10");
    await user.click(screen.getByTestId("render-view-submit"));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
