import { HttpResponse, http } from "msw";
import { simbadReferencesResponse } from "../data/simbad";

export const simbadHandlers = [
  http.get("http://localhost:8000/image/:recordId/simbad-references", () => {
    return HttpResponse.json(simbadReferencesResponse);
  }),
];
