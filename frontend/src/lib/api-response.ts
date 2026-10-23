type ApiResponse<T> =
  | { status: 200; data: T }
  | { status: number; data: unknown };

/** Reads the payload of a successful generated-client response. */
export function okData<T>(response: ApiResponse<T> | undefined): T | undefined {
  if (response?.status !== 200) {
    return undefined;
  }
  return response.data as T;
}
