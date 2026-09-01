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

    expect(screen.getByText("m31")).toBeInTheDocument();
    expect(screen.getByText("b6693c65…")).toBeInTheDocument();
    expect(screen.getByText(/View image/)).toBeInTheDocument();
  });

  it("calls onSelect with record_id on click", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<ImageListItem record={record} onSelect={onSelect} />);

    await user.click(screen.getByRole("button"));

    expect(onSelect).toHaveBeenCalledWith(record.record_id);
  });
});
