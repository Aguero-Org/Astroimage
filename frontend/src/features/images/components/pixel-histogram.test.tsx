import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { PixelHistogram } from "./pixel-histogram";

const SAMPLE = {
  bin_centers: [0, 1, 2, 3],
  counts: [1, 4, 2, 1],
  minimum: 0,
  maximum: 3,
};

describe("PixelHistogram", () => {
  it("renders bars and value range", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <PixelHistogram
          histogram={SAMPLE}
          isPending={false}
          isError={false}
          pmin={1}
          pmax={99}
          showPercentiles
        />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("pixel-histogram")).toBeInTheDocument();
    expect(screen.getByTestId("histogram-min")).toHaveTextContent("0");
    expect(screen.getByTestId("histogram-max")).toHaveTextContent("3");
    expect(
      screen
        .getByTitle("Histograma de píxeles")
        .closest("svg")
        ?.querySelectorAll("rect"),
    ).toHaveLength(4);
  });
});
