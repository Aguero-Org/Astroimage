import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { FitsMetadataSchema } from "@/api/generated/model";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ImageArchive } from "./image-archive";

const SAMPLE: FitsMetadataSchema = {
  source_name: "M31",
  instrument: { telescope: "HST", instrument: "WFC3" },
  image: { shape: [512, 512] },
  wcs: { present: true },
  hdus: {
    selected: 0,
    image_indices: [0],
    images: [{ index: 0, extname: "SCI" }],
  },
  header: { SIMPLE: true },
};

describe("ImageArchive", () => {
  it("groups instrument, image and WCS without dumping JSON", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <ImageArchive info={SAMPLE} isPending={false} />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("archive-instrument")).toBeInTheDocument();
    expect(screen.getByTestId("meta-telescope")).toHaveTextContent("HST");
    expect(screen.getByTestId("meta-shape")).toHaveTextContent("512 × 512");
    expect(screen.getByTestId("meta-wcs-present")).toHaveTextContent("Sí");
    expect(screen.queryByText("{")).not.toBeInTheDocument();
  });
});
