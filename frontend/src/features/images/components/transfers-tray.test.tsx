import { QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createTestQueryClient } from "@/test/render";
import { useTransfersStore } from "../transfers-store";
import { TransfersTray } from "./transfers-tray";

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children }: { children: React.ReactNode }) => (
    <span>{children}</span>
  ),
}));

function resetStore(): void {
  useTransfersStore.setState({ transferIds: [] });
}

function renderTray() {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <TransfersTray />
    </QueryClientProvider>,
  );
}

describe("TransfersTray", () => {
  beforeEach(resetStore);

  it("renders nothing while there are no transfers", () => {
    const { container } = renderTray();

    expect(container).toBeEmptyDOMElement();
  });

  it("renders one feedback per transfer id", async () => {
    act(() => {
      useTransfersStore.getState().add("transfer-1");
      useTransfersStore.getState().add("transfer-2");
    });

    renderTray();

    await waitFor(() => {
      expect(screen.getAllByTestId("transfer-feedback")).toHaveLength(2);
    });
  });

  it("dismisses a transfer from the tray", async () => {
    const user = userEvent.setup();
    act(() => {
      useTransfersStore.getState().add("transfer-1");
    });

    renderTray();

    await screen.findByTestId("transfer-feedback");
    await user.click(
      screen.getByRole("button", { name: "Cerrar seguimiento" }),
    );

    await waitFor(() => {
      expect(screen.queryByTestId("transfer-feedback")).not.toBeInTheDocument();
    });
    expect(useTransfersStore.getState().transferIds).toEqual([]);
  });
});
