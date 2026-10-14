import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ImageTransfer } from "../candidate-api";
import { TransferFeedback } from "./transfer-feedback";

const cancel = vi.fn();
const resume = vi.fn();
const useImageTransfer = vi.fn();

vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    params,
  }: {
    children: React.ReactNode;
    params: { recordId: string; slug?: string };
  }) => (
    <a href={`/image/${params.recordId}/${params.slug ?? ""}`}>{children}</a>
  ),
}));

vi.mock("../candidate-api", async () => {
  const actual =
    await vi.importActual<typeof import("../candidate-api")>(
      "../candidate-api",
    );
  return {
    ...actual,
    useImageTransfer: (...args: unknown[]) => useImageTransfer(...args),
    useCancelTransfer: () => ({ mutateAsync: cancel }),
    useResumeTransfer: () => ({ mutateAsync: resume }),
  };
});

function transfer(overrides: Partial<ImageTransfer> = {}): ImageTransfer {
  return {
    transfer_id: "transfer-1",
    status: "transferring",
    display_name: "Andrómeda",
    product_filename: "product.fits",
    bytes_transferred: 512,
    total_bytes: 1024,
    speed_bytes_per_second: 256,
    progress: 0.5,
    error: null,
    record_id: null,
    slug: null,
    resumable: false,
    ...overrides,
  };
}

function show(body: ImageTransfer | null) {
  useImageTransfer.mockReturnValue(
    body === null ? { data: undefined } : { data: { status: 200, data: body } },
  );
}

describe("TransferFeedback", () => {
  beforeEach(() => {
    cancel.mockReset();
    resume.mockReset();
  });

  it("renders nothing until the transfer exists", () => {
    show(null);
    const { container } = render(<TransferFeedback transferId="transfer-1" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows progress, the remaining time, and cancels an active transfer", async () => {
    const user = userEvent.setup();
    show(transfer());
    render(<TransferFeedback transferId="transfer-1" />);

    expect(screen.getByText("Andrómeda")).toBeInTheDocument();
    expect(screen.getByText(/Transfiriendo/)).toHaveTextContent("50%");
    expect(screen.getByText(/queda ~2 s/)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveValue(50);

    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(cancel).toHaveBeenCalledWith({ transferId: "transfer-1" });
  });

  it("offers resume and the stored image once the transfer settles", async () => {
    const user = userEvent.setup();
    show(
      transfer({
        status: "failed",
        progress: null,
        speed_bytes_per_second: null,
        total_bytes: null,
        error: "mast down",
        resumable: true,
      }),
    );
    const { rerender } = render(<TransferFeedback transferId="transfer-1" />);

    expect(screen.getByText("mast down")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Cancelar" }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reanudar" }));
    expect(resume).toHaveBeenCalledWith({ transferId: "transfer-1" });

    show(
      transfer({
        status: "completed",
        progress: 1,
        resumable: false,
        record_id: "record-1",
        slug: "andromeda",
      }),
    );
    rerender(<TransferFeedback transferId="transfer-1" />);
    expect(screen.getByRole("link", { name: "Abrir imagen" })).toHaveAttribute(
      "href",
      "/image/record-1/andromeda",
    );
  });
});
