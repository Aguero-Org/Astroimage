export function formatQueryError(error: unknown): string {
  return error instanceof Error ? error.message : "error desconocido";
}
