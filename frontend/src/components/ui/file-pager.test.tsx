import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { FilePager } from "@/components/ui/file-pager";

describe("FilePager", () => {
  it("stays hidden on a single page", () => {
    const { container } = render(
      <FilePager page={1} hasMore={false} onPage={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("moves to the next and previous page", async () => {
    const user = userEvent.setup();
    const onPage = vi.fn();
    render(<FilePager page={2} hasMore onPage={onPage} />);

    await user.click(
      screen.getByRole("link", { name: "Ir a la página siguiente" }),
    );
    await user.click(
      screen.getByRole("link", { name: "Ir a la página anterior" }),
    );

    expect(onPage).toHaveBeenNthCalledWith(1, 3);
    expect(onPage).toHaveBeenNthCalledWith(2, 1);
  });

  it("ignores the disabled edges", async () => {
    const user = userEvent.setup();
    const onPage = vi.fn();
    render(<FilePager page={1} hasMore={false} onPage={onPage} />);
    expect(onPage).not.toHaveBeenCalled();

    render(<FilePager page={1} hasMore onPage={onPage} />);
    await user.click(
      screen.getByRole("link", { name: "Ir a la página anterior" }),
    );
    expect(onPage).not.toHaveBeenCalled();
  });
});
