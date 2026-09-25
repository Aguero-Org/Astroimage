import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MOCK_EXTENDED_SOURCE, MOCK_POINT_SOURCE } from "@/mocks/data/image";
import { SourceSelection } from "./source-selection";

describe("SourceSelection", () => {
  it("shows point-source fields when a marker is selected", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection source={MOCK_POINT_SOURCE} />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("meta-sel-snr")).toHaveTextContent("11.20");
    expect(screen.getByTestId("meta-sel-peak")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-flux")).toBeInTheDocument();
  });

  it("shows extended-source fields when an extended marker is selected", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection source={MOCK_EXTENDED_SOURCE} />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("extended-source-selection")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-score")).toHaveTextContent("0.720");
    expect(screen.getByTestId("meta-sel-width")).toHaveTextContent("24.0 px");
    expect(screen.getByTestId("meta-sel-area")).toHaveTextContent("640 px²");
    expect(screen.getByTestId("meta-sel-mean")).toHaveTextContent("3.200");
  });
});
