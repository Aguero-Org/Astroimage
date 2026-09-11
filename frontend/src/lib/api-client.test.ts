import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/test/server";
import { ApiError, customFetch } from "./api-client";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

describe("customFetch — JSON", () => {
  it("parses a JSON response", async () => {
    server.use(
      http.get(`${baseUrl}/health`, () => {
        return HttpResponse.json({ status: "ok" });
      }),
    );

    const result = await customFetch<{
      data: { status: string };
      status: number;
    }>("/health");

    expect(result.status).toBe(200);
    expect(result.data).toEqual({ status: "ok" });
  });

  it("returns undefined data for 204 No Content", async () => {
    server.use(
      http.delete(`${baseUrl}/items/1`, () => {
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const result = await customFetch<{ data: undefined; status: number }>(
      "/items/1",
      { method: "DELETE" },
    );

    expect(result.status).toBe(204);
    expect(result.data).toBeUndefined();
  });
});

describe("customFetch — binary", () => {
  it("returns an ArrayBuffer for application/fits", async () => {
    const payload = new Uint8Array([0x53, 0x49, 0x4d, 0x50, 0x4c, 0x45]);
    server.use(
      http.get(`${baseUrl}/image/abc`, () => {
        return new HttpResponse(payload, {
          status: 200,
          headers: { "content-type": "application/fits" },
        });
      }),
    );

    const result = await customFetch<{
      data: ArrayBuffer;
      status: number;
    }>("/image/abc");

    expect(result.status).toBe(200);
    expect(result.data).toBeInstanceOf(ArrayBuffer);
    expect(result.data.byteLength).toBe(payload.length);
  });
});

describe("customFetch — text", () => {
  it("returns a string for text/plain", async () => {
    server.use(
      http.get(`${baseUrl}/logs`, () => {
        return new HttpResponse("hello", {
          status: 200,
          headers: { "content-type": "text/plain" },
        });
      }),
    );

    const result = await customFetch<{ data: string; status: number }>("/logs");

    expect(result.data).toBe("hello");
  });
});

describe("customFetch — FormData", () => {
  it("does not force Content-Type application/json on FormData bodies", async () => {
    let receivedContentType: string | null = null;

    server.use(
      http.post(`${baseUrl}/upload`, async ({ request }) => {
        receivedContentType = request.headers.get("content-type");
        return HttpResponse.json({ ok: true });
      }),
    );

    const formData = new FormData();
    formData.append("file", new Blob(["data"]), "test.fits");

    await customFetch("/upload", { method: "POST", body: formData });

    expect(receivedContentType).not.toBeNull();
    expect(receivedContentType).toContain("multipart/form-data");
  });
});

describe("customFetch — errors", () => {
  it("throws ApiError with parsed body on non-ok JSON error", async () => {
    server.use(
      http.get(`${baseUrl}/items/404`, () => {
        return HttpResponse.json({ detail: "Not found" }, { status: 404 });
      }),
    );

    await expect(customFetch("/items/404")).rejects.toSatisfy(
      (error: unknown) => {
        return (
          error instanceof ApiError &&
          error.status === 404 &&
          error.body != null
        );
      },
    );
  });
});
