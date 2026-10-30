import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { createElement, type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  getGetImageTransferQueryKey,
  getListHubbleImagesQueryKey,
} from "@/api/generated/hub/hub";
import type { TransferStatusSchema } from "@/api/generated/model";
import { createTestQueryClient, renderHookWithQuery } from "@/test/render";
import { server } from "@/test/server";
import { useImageRecords } from "./api";
import { useImageTransfer } from "./candidate-api";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const transferPayload: TransferStatusSchema = {
  transfer_id: "transfer-1",
  status: "transferring",
  display_name: "Imagen",
  product_filename: "archivo.fits",
  bytes_transferred: 512,
  total_bytes: 1024,
  speed_bytes_per_second: 256,
  progress: 0.5,
  error: null,
  record_id: null,
  slug: null,
  resumable: false,
};

describe("useImageRecords", () => {
  it("returns filtered records for a query", async () => {
    const { result } = renderHookWithQuery(() => useImageRecords("orion"));

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const records = result.current.data?.records ?? [];
    expect(records).toHaveLength(1);
    expect(records[0]?.record_id).toBe("m42");
  });

  it("returns all records when query is empty", async () => {
    const { result } = renderHookWithQuery(() => useImageRecords(""));

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const records = result.current.data?.records ?? [];
    expect(records).toHaveLength(4);
  });

  it("returns empty records for no matches", async () => {
    const { result } = renderHookWithQuery(() =>
      useImageRecords("nonexistent"),
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const records = result.current.data?.records ?? [];
    expect(records).toEqual([]);
  });
});

describe("useImageTransfer", () => {
  it("invalidates the image list once the transfer completes", async () => {
    let requests = 0;
    server.use(
      http.get(`${apiBaseUrl}/image/transfers/:transferId`, () => {
        requests += 1;
        return HttpResponse.json({
          ...transferPayload,
          status: requests === 1 ? "transferring" : "completed",
          progress: requests === 1 ? 0.5 : 1,
        });
      }),
    );

    const queryClient = createTestQueryClient();
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    const wrapper = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children);
    const { result } = renderHook(() => useImageTransfer("transfer-1"), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.data?.status).toBe("transferring");
    });
    expect(invalidate).not.toHaveBeenCalled();

    await queryClient.refetchQueries({
      queryKey: getGetImageTransferQueryKey("transfer-1"),
    });

    await waitFor(() => {
      expect(result.current.data?.status).toBe("completed");
    });
    await waitFor(() => {
      expect(invalidate).toHaveBeenCalledTimes(1);
    });
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: getListHubbleImagesQueryKey(),
    });
  });
});
