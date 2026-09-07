import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { HduSelector } from "./hdu-selector";

describe("HduSelector", () => {
  it("hides when there is a single image HDU", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <HduSelector
          images={[{ index: 0, extname: "SCI" }]}
          value={0}
          onChange={vi.fn()}
        />
      </TooltipProvider>,
    );

    expect(screen.queryByTestId("hdu-selector")).not.toBeInTheDocument();
  });

  it("lets the user pick among image HDUs", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <HduSelector
          images={[
            { index: 1, extname: "SCI" },
            { index: 2, extname: "ERR" },
          ]}
          value={1}
          onChange={onChange}
        />
      </TooltipProvider>,
    );

    await user.click(screen.getByTestId("hdu-selector"));
    await user.click(screen.getByTestId("hdu-option-2"));
    expect(onChange).toHaveBeenCalledWith(2);
  });
});
