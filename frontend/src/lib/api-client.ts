function apiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
}

async function parseResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  if (contentType.startsWith("text/")) {
    return response.text();
  }

  if (contentType.includes("application/fits")) {
    return response.arrayBuffer();
  }

  return response.blob();
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    super(`API error ${status}: ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export async function customFetch<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const { body, headers: customHeaders, ...restOptions } = options ?? {};

  const headers = new Headers(customHeaders);
  if (!(body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${apiBaseUrl()}${url}`, {
    ...restOptions,
    body,
    headers,
  });

  const data = await parseResponseBody(response);

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText, data);
  }

  return { data, status: response.status, headers: response.headers } as T;
}
