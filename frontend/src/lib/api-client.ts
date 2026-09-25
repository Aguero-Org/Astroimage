function apiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
}

const CLIENT_ID_STORAGE_KEY = "astroimage.client-id";

function fallbackUuid(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = Math.floor(Math.random() * 16);
    const value = char === "x" ? random : (random % 4) + 8;
    return value.toString(16);
  });
}

function clientId(): string {
  const stored = localStorage.getItem(CLIENT_ID_STORAGE_KEY);
  if (stored) {
    return stored;
  }
  const generated = crypto.randomUUID?.() ?? fallbackUuid();
  localStorage.setItem(CLIENT_ID_STORAGE_KEY, generated);
  return generated;
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

  const isFormData = body instanceof FormData;
  const isSearchParams = body instanceof URLSearchParams;
  const headers = new Headers(customHeaders);
  headers.set("X-Client-Id", clientId());
  if (!isFormData && !isSearchParams && !headers.has("Content-Type")) {
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
