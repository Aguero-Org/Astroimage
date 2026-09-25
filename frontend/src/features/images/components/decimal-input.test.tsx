import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { DecimalInput } from "./decimal-input";

function Harness() {
  const [value, setValue] = useState("50");
  return (
    <DecimalInput
      id="sample"
      testId="sample-input"
      value={value}
      onValueChange={setValue}
    />
  );
}

describe("DecimalInput", () => {
  it("can be cleared without inserting a zero", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const field = screen.getByTestId("sample-input");
    await user.click(field);
    await user.keyboard("{End}{Backspace}{Backspace}");
    expect(field).toHaveValue("");
    await user.type(field, "0.5");
    expect(field).toHaveValue("0.5");
  });
});
