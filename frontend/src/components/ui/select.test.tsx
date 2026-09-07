import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Select } from "./select";

describe("Select", () => {
  it("renders a native select with the shared slot", async () => {
    const user = userEvent.setup();
    render(
      <Select data-testid="ui-select" defaultValue="grey">
        <option value="grey">Gris</option>
        <option value="heat">Calor</option>
      </Select>,
    );

    const field = screen.getByTestId("ui-select");
    expect(field.tagName).toBe("SELECT");
    expect(field).toHaveAttribute("data-slot", "select");
    await user.selectOptions(field, "heat");
    expect(field).toHaveValue("heat");
  });
});
