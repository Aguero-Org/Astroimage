import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MOCK_POINT_SOURCE } from "@/mocks/data/image";
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
});
