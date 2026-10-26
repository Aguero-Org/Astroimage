import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  LAST_IMAGE_RECORD_KEY,
  rememberLastImageRecord,
} from "@/features/images/last-record";
import { renderWithRouter } from "@/test/router";

describe("GlossaryPage", () => {
  afterEach(() => {
    sessionStorage.removeItem(LAST_IMAGE_RECORD_KEY);
    document.title = "";
  });

  it("groups entries and filters by name", async () => {
    const user = userEvent.setup();
    renderWithRouter("/glossary");

    await waitFor(() => {
      expect(screen.getByTestId("glossary-page")).toBeInTheDocument();
    });
    expect(screen.getByTestId("glossary-group-vista")).toBeInTheDocument();
    expect(screen.getByTestId("glossary-entry-fwhm")).toBeInTheDocument();

    await user.type(screen.getByTestId("glossary-search"), "FWHM");
    expect(screen.getByTestId("glossary-entry-fwhm")).toBeInTheDocument();
    expect(
      screen.queryByTestId("glossary-entry-stretch"),
    ).not.toBeInTheDocument();
  });

  it("highlights the hashed entry and copies its link", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    renderWithRouter("/glossary#fwhm");

    await waitFor(() => {
      expect(screen.getByTestId("glossary-entry-fwhm")).toBeInTheDocument();
    });
    expect(screen.getByTestId("glossary-entry-fwhm")).toHaveAttribute(
      "data-active",
      "true",
    );
    expect(document.title).toBe("FWHM - Astroimage");
    expect(screen.getByTestId("glossary-toc")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Fuentes" })).toHaveAttribute(
      "data-active",
      "true",
    );
    await user.click(screen.getByTestId("glossary-copy-fwhm"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("/glossary#fwhm"),
    );
  });

  it("links back to the last opened viewer", async () => {
    rememberLastImageRecord("m31");
    renderWithRouter("/glossary");

    await waitFor(() => {
      expect(screen.getByTestId("glossary-back-to-viewer")).toHaveAttribute(
        "href",
        "/image/m31",
      );
    });
  });
});
