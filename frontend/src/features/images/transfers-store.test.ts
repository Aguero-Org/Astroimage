import { afterEach, describe, expect, it } from "vitest";
import { useTransfersStore } from "./transfers-store";

function resetStore(): void {
  useTransfersStore.setState({ transferIds: [] });
}

describe("useTransfersStore", () => {
  afterEach(resetStore);

  it("adds transfers without duplicating ids", () => {
    useTransfersStore.getState().add("transfer-1");
    useTransfersStore.getState().add("transfer-1");
    useTransfersStore.getState().add("transfer-2");

    expect(useTransfersStore.getState().transferIds).toEqual([
      "transfer-1",
      "transfer-2",
    ]);
  });

  it("removes only the requested transfer", () => {
    useTransfersStore.getState().add("transfer-1");
    useTransfersStore.getState().add("transfer-2");

    useTransfersStore.getState().remove("transfer-1");

    expect(useTransfersStore.getState().transferIds).toEqual(["transfer-2"]);
  });
});
