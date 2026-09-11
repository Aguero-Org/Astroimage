import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { useThemeStore } from "@/lib/theme-store";
import { ThemeToggle } from "./theme-toggle";

describe("ThemeToggle", () => {
  it("toggles the dark class on the document", async () => {
    useThemeStore.setState({ theme: "light" });
    document.documentElement.classList.remove("dark");
    const user = userEvent.setup();
    render(<ThemeToggle />);

    expect(screen.getByTestId("theme-toggle")).toHaveAttribute(
      "aria-label",
      "Cambiar a tema oscuro",
    );
    await user.click(screen.getByTestId("theme-toggle"));
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(useThemeStore.getState().theme).toBe("dark");
  });
});
