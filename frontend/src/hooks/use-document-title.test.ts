import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useDocumentTitle } from "./use-document-title";

describe("useDocumentTitle", () => {
  afterEach(() => {
    document.title = "";
  });

  it("sets the title and restores the fallback on unmount", () => {
    const { unmount } = renderHook(() =>
      useDocumentTitle("M31 - Astroimage", "Astroimage 🌌"),
    );

    expect(document.title).toBe("M31 - Astroimage");

    unmount();
    expect(document.title).toBe("Astroimage 🌌");
  });
});
