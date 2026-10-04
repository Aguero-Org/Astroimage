import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MetadataGroup } from "./metadata-group";

describe("MetadataGroup", () => {
  it("copies one value and the whole group", async () => {
    const user = userEvent.setup();
    const writeText = vi
      .spyOn(navigator.clipboard, "writeText")
      .mockResolvedValue();
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

    await user.click(screen.getByTestId("copy-meta-sel-gaia-id"));
    await user.click(
      screen.getByTestId("copy-group-archive-extended-selection"),
    );

    expect(writeText).toHaveBeenNthCalledWith(1, "1156995577441004288");
    expect(writeText).toHaveBeenNthCalledWith(
      2,
      "Gaia source: 1156995577441004288",
    );
  });
});
