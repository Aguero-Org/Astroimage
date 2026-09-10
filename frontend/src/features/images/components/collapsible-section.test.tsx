import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CollapsibleSection } from "./collapsible-section";

describe("CollapsibleSection", () => {
  it("starts closed and reveals content on toggle", async () => {
    const user = userEvent.setup();
    render(
      <CollapsibleSection id="view" title="Vista">
        <p>Parámetros de render</p>
      </CollapsibleSection>,
    );

    expect(screen.getByTestId("inspector-section-view")).toBeInTheDocument();
    expect(screen.queryByText("Parámetros de render")).not.toBeInTheDocument();

    await user.click(screen.getByTestId("inspector-section-view-toggle"));
    expect(screen.getByText("Parámetros de render")).toBeVisible();
  });

  it("can start open", () => {
    render(
      <CollapsibleSection id="sources" title="Fuentes" defaultOpen>
        <p>Formulario</p>
      </CollapsibleSection>,
    );

    expect(screen.getByText("Formulario")).toBeVisible();
  });
});
