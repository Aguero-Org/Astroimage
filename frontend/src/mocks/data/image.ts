export type MockImageSummary = {
  id: string;
  name: string;
  object: string;
  ra: number;
  dec: number;
  width: number;
  height: number;
  exposure: number;
  filter: string;
  instrument: string;
  dateObs: string;
};

export type MockImageInfo = MockImageSummary & {
  pixelScale: number;
  binning: number;
  gain: number;
  offset: number;
  temperature: number;
  frames: number;
};

export const mockImages: MockImageInfo[] = [
  {
    id: "m31",
    name: "M31 - Andromeda Galaxy",
    object: "M31",
    ra: 10.6847,
    dec: 41.2687,
    width: 4096,
    height: 4096,
    exposure: 3600,
    filter: "L",
    instrument: "ASI6200MM",
    dateObs: "2024-12-15T22:30:00Z",
    pixelScale: 0.8,
    binning: 1,
    gain: 100,
    offset: 10,
    temperature: -15,
    frames: 30,
  },
  {
    id: "m42",
    name: "M42 - Orion Nebula",
    object: "M42",
    ra: 83.8221,
    dec: -5.3911,
    width: 2048,
    height: 2048,
    exposure: 1800,
    filter: "HA",
    instrument: "ASI6200MM",
    dateObs: "2024-12-20T01:15:00Z",
    pixelScale: 1.6,
    binning: 2,
    gain: 200,
    offset: 50,
    temperature: -10,
    frames: 45,
  },
  {
    id: "ngc6992",
    name: "NGC 6992 - Veil Nebula",
    object: "NGC6992",
    ra: 313.0833,
    dec: 31.7167,
    width: 4096,
    height: 4096,
    exposure: 2400,
    filter: "OIII",
    instrument: "ASI6200MM",
    dateObs: "2024-11-10T23:45:00Z",
    pixelScale: 0.8,
    binning: 1,
    gain: 100,
    offset: 10,
    temperature: -15,
    frames: 20,
  },
  {
    id: "ic1396",
    name: "IC 1396 - Elephant Trunk Nebula",
    object: "IC1396",
    ra: 324.7,
    dec: 57.5,
    width: 2048,
    height: 2048,
    exposure: 3000,
    filter: "SII",
    instrument: "ASI6200MM",
    dateObs: "2024-10-05T20:00:00Z",
    pixelScale: 1.6,
    binning: 2,
    gain: 200,
    offset: 50,
    temperature: -10,
    frames: 15,
  },
];

export function findImage(id: string): MockImageInfo | undefined {
  return mockImages.find((img) => img.id === id);
}

export function searchImages(query: string): MockImageSummary[] {
  const normalized = query.toLowerCase().trim();
  if (normalized === "") {
    return mockImages;
  }
  return mockImages.filter(
    (img) =>
      img.name.toLowerCase().includes(normalized) ||
      img.object.toLowerCase().includes(normalized) ||
      img.id.toLowerCase().includes(normalized),
  );
}
