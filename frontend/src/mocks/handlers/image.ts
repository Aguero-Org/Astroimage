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

  http.get(`${apiBaseUrl}/image/:recordId/sources`, ({ params }) => {
    const record = findRecord(params.recordId as string);
    if (!record) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json({
      source_name: record.name,
      summary: { point_count: 1, extended_count: 1 },
      point_sources: [
        {
          source_id: 1,
          rank: 1,
          xcentroid: 12.5,
          ycentroid: 8.25,
          snr: 11.2,
          relevance_score: 0.64,
          object_type: "point",
        },
      ],
      extended_sources: [
        {
          source_id: 101,
          rank: 1,
          xcentroid: 90.25,
          ycentroid: 55.5,
          snr: 5400,
          peak: 42.1,
          object_type: "extended",
        },
      ],
    });
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
    const png = new Uint8Array([
      0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
      0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
      0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4, 0x89, 0x00, 0x00, 0x00,
      0x0a, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00,
      0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4, 0x00, 0x00, 0x00, 0x00, 0x49,
      0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
    ]);
    return new HttpResponse(png, {
      status: 200,
      headers: {
        "content-type": "image/png",
        "content-disposition": `inline; filename="${record.record_id}.png"`,
      },
    });
  }),
];
