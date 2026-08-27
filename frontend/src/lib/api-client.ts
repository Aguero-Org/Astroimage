function apiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
}

export async function customFetch<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  const contentType = response.headers.get("content-type") ?? "";
  const data =
    response.status === 204 || !contentType.includes("application/json")
      ? undefined
      : await response.json();

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return { data, status: response.status, headers: response.headers } as T;
}
