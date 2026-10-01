import { HttpResponse, http } from "msw";
import {
  filterRecords,
  findRecord,
  mockRecords,
  mockSourceDetection,
} from "../data/image";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const imageHandlers = [
  http.get(`${apiBaseUrl}/image`, ({ request }) => {
    const url = new URL(request.url);
    const cuerpoCeleste = url.searchParams.get("cuerpo_celeste");
    const records = filterRecords(cuerpoCeleste);
    return HttpResponse.json({
      records,
      page: Number(url.searchParams.get("page") ?? "1"),
      limit: Number(url.searchParams.get("limit") ?? "8"),
      has_more: false,
      sort: url.searchParams.get("sort") ?? "created_at",
      order: url.searchParams.get("order") ?? "desc",
    });
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
    return HttpResponse.json({
      items: [
        {
          token: `token-${match.record_id}`,
          product_filename: `${match.record_id}.fits`,
          instrument: "WFC3",
          proposal_id: "12345",
          observation_id: match.record_id,
          filters: "F606W",
          observed_at: null,
          size_bytes: 120 * 1024 * 1024,
          ra_deg: 0,
          dec_deg: 0,
          data_uri: `mast:HST/product/${match.record_id}.fits`,
        },
      ],
      page: 1,
      limit: 8,
      has_more: false,
      sort: url.searchParams.get("sort") ?? "product_filename",
      order: url.searchParams.get("order") ?? "asc",
    });
  }),

  http.post(`${apiBaseUrl}/image/search/select`, async ({ request }) => {
    const body = (await request.json()) as {
      candidate_token: string;
      display_name?: string;
    };
    return HttpResponse.json({
      transfer_id: body.candidate_token,
      status: "completed",
      display_name: body.display_name ?? "",
      product_filename: `${body.candidate_token}.fits`,
      bytes_transferred: 120 * 1024 * 1024,
      total_bytes: 120 * 1024 * 1024,
      speed_bytes_per_second: null,
      progress: 1,
      error: null,
      record_id: "m42",
      slug: "m42",
      resumable: false,
    });
  }),

  http.get(`${apiBaseUrl}/image/transfers/:transferId`, ({ params }) => {
    return HttpResponse.json({
      transfer_id: params.transferId,
      status: "completed",
      display_name: "Imagen",
      product_filename: "archivo.fits",
      bytes_transferred: 120 * 1024 * 1024,
      total_bytes: 120 * 1024 * 1024,
      speed_bytes_per_second: null,
      progress: 1,
      error: null,
      record_id: "m42",
      slug: "m42",
      resumable: false,
    });
  }),

  http.get(`${apiBaseUrl}/image/:recordId/sources`, ({ params }) => {
    const record = findRecord(params.recordId as string);
    if (!record) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json(mockSourceDetection(record));
  }),

  http.get(`${apiBaseUrl}/image/:recordId/histogram`, ({ params }) => {
    const record = findRecord(params.recordId as string);
    if (!record) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json({
      bin_centers: [0, 1, 2, 3, 4, 5, 6, 7],
      counts: [2, 5, 12, 20, 18, 9, 4, 1],
      minimum: 0,
      maximum: 7,
    });
  }),

  http.get(`${apiBaseUrl}/image/:recordId/info`, ({ params }) => {
    const record = findRecord(params.recordId as string);
    if (!record) {
      return HttpResponse.json({ detail: "Image not found" }, { status: 404 });
    }
    return HttpResponse.json({
      source_name: record.name,
      instrument: {
        telescope: "HST",
        instrument: "WFC3",
        filter_name: "F606W",
        exptime: 580.0,
      },
      image: { shape: [1024, 1024], unit: "e-/s" },
      wcs: { present: true, naxis: 2, ctype: ["RA---TAN", "DEC--TAN"] },
      hdus: {
        selected: 1,
        image_indices: [1, 2],
        images: [
          { index: 1, extname: "SCI", kind: "image", shape: [1024, 1024] },
          { index: 2, extname: "ERR", kind: "image", shape: [1024, 1024] },
        ],
      },
      header: { TELESCOP: "HST", INSTRUME: "WFC3" },
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
