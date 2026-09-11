import { HttpResponse, http } from "msw";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const healthHandlers = [
  http.get(`${apiBaseUrl}/health`, () => {
    return HttpResponse.json({ status: "ok" });
  }),
];
