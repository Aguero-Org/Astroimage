import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";
import { server } from "@/test/server";
import { ApiError, customFetch } from "./api-client";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("customFetch — JSON", () => {
  it("uses the local API when the base URL is unset", async () => {
    vi.stubEnv("VITE_API_BASE_URL", undefined);
    server.use(
      http.get("http://localhost:8000/health", () => {
        return HttpResponse.json({ status: "ok" });
      }),
    );

    const result = await customFetch<{ status: string }>("/health");

    expect(result).toEqual({ status: "ok" });
  });

  it("parses a JSON response", async () => {
    server.use(
      http.get(`${baseUrl}/health`, () => {
        return HttpResponse.json({ status: "ok" });
      }),
    );

    const result = await customFetch<{ status: string }>("/health");

    expect(result).toEqual({ status: "ok" });
  });

  it("returns undefined data for 204 No Content", async () => {
    server.use(
      http.delete(`${baseUrl}/items/1`, () => {
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const result = await customFetch<undefined>("/items/1", {
      method: "DELETE",
    });

    expect(result).toBeUndefined();
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

    const result = await customFetch<ArrayBuffer>("/image/abc");

    expect(result).toBeInstanceOf(ArrayBuffer);
    expect(result.byteLength).toBe(payload.length);
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

    const result = await customFetch<string>("/logs");

    expect(result).toBe("hello");
  });
});

describe("customFetch — content type", () => {
  it("sets application/json for regular bodies", async () => {
    let receivedContentType: string | null = null;
    server.use(
      http.post(`${baseUrl}/items`, async ({ request }) => {
        receivedContentType = request.headers.get("content-type");
        return HttpResponse.json({ ok: true });
      }),
    );

    await customFetch("/items", {
      method: "POST",
      body: JSON.stringify({ name: "M31" }),
    });

    expect(receivedContentType).toBe("application/json");
  });

  it("keeps an explicitly provided content type", async () => {
    let receivedContentType: string | null = null;
    server.use(
      http.post(`${baseUrl}/items`, async ({ request }) => {
        receivedContentType = request.headers.get("content-type");
        return HttpResponse.json({ ok: true });
      }),
    );

    await customFetch("/items", {
      method: "POST",
      body: JSON.stringify({ name: "M31" }),
      headers: { "Content-Type": "application/vnd.api+json" },
    });

    expect(receivedContentType).toBe("application/vnd.api+json");
  });

  it("falls back to a Blob when the response has no content type", async () => {
    server.use(
      http.get(`${baseUrl}/raw`, () => {
        return new HttpResponse(new Uint8Array([1, 2]));
      }),
    );

    const result = await customFetch<Blob>("/raw");

    expect(result.size).toBe(2);
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

  it("describes the failure on the ApiError instance", async () => {
    server.use(
      http.get(`${baseUrl}/items/500`, () => {
        return HttpResponse.json({ detail: "boom" }, { status: 500 });
      }),
    );

    const error = await customFetch("/items/500").catch((reason: unknown) => {
      return reason;
    });

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      name: "ApiError",
      status: 500,
      body: { detail: "boom" },
    });
    expect((error as Error).message).toContain("500");
  });
});

describe("customFetch — client id", () => {
  it("generates the client id once and reuses it", async () => {
    localStorage.clear();
    const received: string[] = [];
    server.use(
      http.get(`${baseUrl}/health`, ({ request }) => {
        received.push(request.headers.get("x-client-id") ?? "");
        return HttpResponse.json({ status: "ok" });
      }),
    );

    await customFetch("/health");
    await customFetch("/health");

    expect(received[0]).not.toBe("");
    expect(received[1]).toBe(received[0]);
    expect(localStorage.getItem("astroimage.client-id")).toBe(received[0]);
  });
});

describe("customFetch — other bodies", () => {
  it("keeps the URLSearchParams content type", async () => {
    let receivedContentType: string | null = null;
    server.use(
      http.post(`${baseUrl}/token`, async ({ request }) => {
        receivedContentType = request.headers.get("content-type");
        return HttpResponse.json({ ok: true });
      }),
    );

    await customFetch("/token", {
      method: "POST",
      body: new URLSearchParams({ grant: "code" }),
    });

    expect(receivedContentType).toContain("application/x-www-form-urlencoded");
  });

  it("returns a Blob for unknown content types", async () => {
    server.use(
      http.get(`${baseUrl}/download`, () => {
        return new HttpResponse(new Uint8Array([1, 2, 3]), {
          status: 200,
          headers: { "content-type": "application/octet-stream" },
        });
      }),
    );

    const result = await customFetch<Blob>("/download");

    expect(result.size).toBe(3);
    expect(await result.text()).toHaveLength(3);
  });
});
