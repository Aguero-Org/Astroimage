import { HttpResponse, http } from "msw";
import { mockCatalogRecommendation } from "../data/catalogs";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const catalogHandlers = [
  http.get(`${apiBaseUrl}/image/:recordId/catalogs/recommendations`, () =>
    HttpResponse.json(mockCatalogRecommendation()),
  ),
  http.get(
    `${apiBaseUrl}/image/:recordId/catalogs/recommendations/jobs/:jobId`,
    () => HttpResponse.json(mockCatalogRecommendation()),
  ),
];
