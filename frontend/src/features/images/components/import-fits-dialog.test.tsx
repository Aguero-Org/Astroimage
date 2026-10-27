import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderWithRouter } from "@/test/router";

describe("ImportFitsControl", () => {
  it("uploads a local fits file from the home list", async () => {
    const user = userEvent.setup();
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByTestId("import-fits")).toBeInTheDocument();
    });
    await user.click(screen.getByTestId("import-fits"));
    const input = screen.getByTestId("import-fits-files");
    await user.upload(
      input,
      new File([new Uint8Array([1, 2, 3])], "local.fits", {
        type: "application/fits",
      }),
    );
    await user.click(screen.getByTestId("confirm-import-fits"));

    await waitFor(() => {
      expect(
        screen.queryByTestId("confirm-import-fits"),
      ).not.toBeInTheDocument();
    });
  });

  it("opens the import when a file is dragged and keeps the dropped fits", async () => {
    renderWithRouter();
    await waitFor(() => {
      expect(screen.getByTestId("import-fits")).toBeInTheDocument();
    });

    const dropped = new File([new Uint8Array([1])], "dropped.fits");
    const dataTransfer = {
      types: ["Files"],
      files: [dropped],
      dropEffect: "none",
    };
    fireEvent.dragEnter(window, { dataTransfer });
    expect(screen.getByTestId("import-fits-dropzone")).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    fireEvent.drop(window, { dataTransfer });
    expect(screen.getByText(/dropped\.fits/)).toBeInTheDocument();
    expect(
      screen.queryByTestId("import-fits-dropzone"),
    ).not.toBeInTheDocument();
  });

  it("rejects a link that is not http or https", async () => {
    const user = userEvent.setup();
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByTestId("import-fits")).toBeInTheDocument();
    });
    await user.click(screen.getByTestId("import-fits"));
    await user.click(screen.getByTestId("import-fits-source-url"));
    await user.type(screen.getByTestId("import-fits-url"), "nebula.fits");
    await user.click(screen.getByTestId("confirm-import-fits"));

    expect(
      screen.getByText(
        "El enlace tiene que ser http, https o un URI de MAST (mast:).",
      ),
    ).toBeInTheDocument();
  });
});
