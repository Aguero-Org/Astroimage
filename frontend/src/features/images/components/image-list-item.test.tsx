import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ImageRecord } from "../types";
import { ImageListItem } from "./image-list-item";

const record: ImageRecord = {
  record_id: "b6693c65-1f3f-4169-a741-a9fc2ef1a36b",
  name: "m31",
};

describe("ImageListItem", () => {
  it("renders record name and truncated id", () => {
    render(<ImageListItem record={record} onSelect={vi.fn()} />);

    const item = screen.getByTestId("image-list-item");
    expect(item).toHaveTextContent("m31");
    expect(item).toHaveTextContent("b6693c65…");
    expect(item).toHaveTextContent("Ver imagen");
  });

  it("calls onSelect with record_id on click", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<ImageListItem record={record} onSelect={onSelect} />);

    await user.click(screen.getByTestId("image-list-item-open"));

    expect(onSelect).toHaveBeenCalledWith(record.record_id);
  });
});
