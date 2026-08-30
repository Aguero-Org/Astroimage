function apiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
}

export async function customFetch<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const isFormData = options?.body instanceof FormData;
  const isSearchParams = options?.body instanceof URLSearchParams;
  const headers = new Headers(options?.headers);
  if (!isFormData && !isSearchParams && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${apiBaseUrl()}${url}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") ?? "";
  const data =
    response.status === 204
      ? undefined
      : contentType.includes("application/json")
        ? await response.json()
        : await response.blob();

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return { data, status: response.status, headers: response.headers } as T;
}
