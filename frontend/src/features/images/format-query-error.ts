import { ApiError } from "@/lib/api-client";

export function formatQueryError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return "No encontrado.";
    }
    if (error.status === 422) {
      return "Esos datos no son válidos.";
    }
    if (error.status >= 500 && error.status < 600) {
      return "No se pudo completar. Probá de nuevo.";
    }
    if (error.status >= 400 && error.status < 500) {
      return `Error ${error.status}.`;
    }
  }
  return error instanceof Error ? error.message : "error desconocido";
}
