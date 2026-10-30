import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ImportNameDialog } from "./import-name-dialog";

function renderDialog(
  onConfirm = vi.fn(),
  filename: string | null = "andromeda.fits",
  onCancel = vi.fn(),
) {
  return {
    onConfirm,
    onCancel,
    user: userEvent.setup(),
    ...render(
      <ImportNameDialog
        filename={filename}
        submitting={false}
        onCancel={onCancel}
        onConfirm={onConfirm}
      />,
    ),
  };
}

describe("ImportNameDialog", () => {
  it("submits the trimmed display name", async () => {
    const { onConfirm, user } = renderDialog();

    await user.type(
      screen.getByLabelText("Nombre descriptivo"),
      "  Núcleo de Andrómeda  ",
    );
    await user.click(screen.getByTestId("confirm-import-name"));

    expect(onConfirm).toHaveBeenCalledWith("Núcleo de Andrómeda");
  });

  it("does not allow importing an empty name", async () => {
    const { onConfirm, user } = renderDialog();

    expect(screen.getByTestId("confirm-import-name")).toBeDisabled();
    await user.type(screen.getByLabelText("Nombre descriptivo"), "   ");
    expect(screen.getByTestId("confirm-import-name")).toBeDisabled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("stays closed without a filename", () => {
    renderDialog(vi.fn(), null);

    expect(screen.queryByText("Nombre de la imagen")).not.toBeInTheDocument();
  });

  it("cancels and resets the form when dismissed", async () => {
    const { onCancel, user } = renderDialog();
    const input = screen.getByLabelText("Nombre descriptivo");

    await user.type(input, "Temporal");
    await user.keyboard("{Escape}");

    await waitFor(() => expect(onCancel).toHaveBeenCalledTimes(1));
  });
});
