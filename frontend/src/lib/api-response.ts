type ApiResponse<T> =
  | { status: 200; data: T }
  | { status: number; data: unknown };

export function okData<T>(response: ApiResponse<T> | undefined): T | undefined {
  if (response?.status !== 200) {
    return undefined;
  }
  return response.data as T;
}
