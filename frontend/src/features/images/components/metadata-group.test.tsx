import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MetadataGroup } from "./metadata-group";

describe("MetadataGroup", () => {
  it("copies one value and the whole group", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(
      <TooltipProvider>
        <MetadataGroup
          title="Fuente extendida 2"
          testId="archive-extended-selection"
          rows={[
            {
              id: "sel-gaia-id",
              label: "Gaia source",
              value: "1156995577441004288",
              help: "Identificador.",
              glossaryId: "gaia",
            },
          ]}
        />
      </TooltipProvider>,
    );

    fireEvent.click(screen.getByTestId("copy-meta-sel-gaia-id"));
    fireEvent.click(
      screen.getByTestId("copy-group-archive-extended-selection"),
    );

    expect(writeText).toHaveBeenNthCalledWith(1, "1156995577441004288");
    expect(writeText).toHaveBeenNthCalledWith(
      2,
      "Gaia source: 1156995577441004288",
    );
  });
});
