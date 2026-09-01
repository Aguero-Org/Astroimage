import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ImageRecord } from "../types";
import { ImageListItem } from "./image-list-item";

const record: ImageRecord = {
  record_id: "m31",
  name: "M31 - Andromeda Galaxy",
};

describe("ImageListItem", () => {
  it("renders record name and id", () => {
    render(<ImageListItem record={record} />);

    expect(screen.getByText("M31 - Andromeda Galaxy")).toBeInTheDocument();
    expect(screen.getByText("m31")).toBeInTheDocument();
  });
});
