import { HttpResponse, http } from "msw";
import { filterRecords, findRecord, mockRecords } from "../data/image";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const imageHandlers = [
  http.get(`${apiBaseUrl}/image`, ({ request }) => {
    const url = new URL(request.url);
    const cuerpoCeleste = url.searchParams.get("cuerpo_celeste");
    return HttpResponse.json({ records: filterRecords(cuerpoCeleste) });
  }),

  http.get(`${apiBaseUrl}/image/search`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get("query") ?? "";
    const normalized = query.toLowerCase().trim();
    const match = mockRecords.find((record) =>
      record.name.toLowerCase().includes(normalized),
    );
    if (!match) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json({ record_id: match.record_id });
  }),

  http.get(`${apiBaseUrl}/image/:recordId/info`, ({ params }) => {
    const record = findRecord(params.recordId as string);
    if (!record) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json({
      source_name: record.name,
      hdus: { selected: 0, image_indices: [0], images: [] },
    });
  }),

  http.get(`${apiBaseUrl}/image/:recordId`, ({ params }) => {
    const record = findRecord(params.recordId as string);
    if (!record) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    const header = new Uint8Array([0x53, 0x49, 0x4d, 0x50, 0x4c, 0x45]);
    return new HttpResponse(header, {
      status: 200,
      headers: {
        "content-type": "application/fits",
        "content-disposition": `inline; filename="${record.record_id}.fits"`,
      },
    });
  }),
];
