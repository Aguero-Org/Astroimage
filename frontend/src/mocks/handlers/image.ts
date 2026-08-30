import { HttpResponse, http } from "msw";
import { findImage, searchImages } from "../data/image";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const imageHandlers = [
  http.get(`${apiBaseUrl}/image`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get("query") ?? "";
    const results = searchImages(query);
    return HttpResponse.json(results);
  }),

  http.get(`${apiBaseUrl}/image/search`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get("query") ?? "";
    const results = searchImages(query);
    return HttpResponse.json(results);
  }),

  http.get(`${apiBaseUrl}/image/:id/info`, ({ params }) => {
    const image = findImage(params.id as string);
    if (!image) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json(image);
  }),

  http.get(`${apiBaseUrl}/image/:id`, ({ params }) => {
    const image = findImage(params.id as string);
    if (!image) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    const header = new Uint8Array([0x53, 0x49, 0x4d, 0x50, 0x4c, 0x45]);
    return new HttpResponse(header, {
      status: 200,
      headers: {
        "content-type": "application/octet-stream",
        "content-disposition": `inline; filename="${image.id}.fits"`,
      },
    });
  }),
];
