import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";

export const handlers = [
  http.get("http://localhost:8000/health", () => {
    return HttpResponse.json({ status: "ok" });
  }),
];

export const server = setupServer(...handlers);
