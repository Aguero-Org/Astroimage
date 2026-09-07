import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./select";

describe("Select", () => {
  it("opens a styled list and picks an option", async () => {
    const user = userEvent.setup();
    render(
      <Select defaultValue="grey">
        <SelectTrigger data-testid="ui-select">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="grey">Gris</SelectItem>
          <SelectItem value="heat" data-testid="ui-select-heat">
            Calor
          </SelectItem>
        </SelectContent>
      </Select>,
    );

    expect(screen.getByTestId("ui-select")).toHaveAttribute(
      "data-slot",
      "select-trigger",
    );
    await user.click(screen.getByTestId("ui-select"));
    expect(screen.getByTestId("select-content")).toBeVisible();
    await user.click(screen.getByTestId("ui-select-heat"));
    expect(screen.getByTestId("ui-select")).toHaveTextContent("Calor");
  });
});
