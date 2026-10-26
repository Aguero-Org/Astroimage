import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api-client";
import { formatQueryError } from "./format-query-error";

describe("formatQueryError", () => {
  it("normalizes a 404", () => {
    expect(formatQueryError(new ApiError(404, "Not Found", null))).toBe(
      "No encontrado.",
    );
  });

  it("normalizes a 422", () => {
    expect(
      formatQueryError(new ApiError(422, "Unprocessable Entity", null)),
    ).toBe("Los datos enviados no son válidos.");
  });

  it("normalizes a 500", () => {
    expect(
      formatQueryError(new ApiError(500, "Internal Server Error", null)),
    ).toBe("El servidor no pudo completar la operación.");
  });

  it("normalizes another 4xx", () => {
    expect(formatQueryError(new ApiError(403, "Forbidden", null))).toBe(
      "Error 403.",
    );
  });

  it("uses the message of a plain Error", () => {
    expect(formatQueryError(new Error("falló la red"))).toBe("falló la red");
  });

  it("falls back for an unknown value", () => {
    expect(formatQueryError("boom")).toBe("error desconocido");
  });
});
