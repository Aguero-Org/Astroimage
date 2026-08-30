import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ImageSummary } from "../types";
import { ImageListItem } from "./image-list-item";

const image: ImageSummary = {
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
};

describe("ImageListItem", () => {
  it("renders image name, filter and dimensions", () => {
    render(<ImageListItem image={image} />);

    expect(screen.getByText("M31 - Andromeda Galaxy")).toBeInTheDocument();
    expect(screen.getByText("L")).toBeInTheDocument();
    expect(screen.getByText(/4096×4096/)).toBeInTheDocument();
    expect(screen.getByText(/3600s.*2024-12-15/)).toBeInTheDocument();
  });
});
