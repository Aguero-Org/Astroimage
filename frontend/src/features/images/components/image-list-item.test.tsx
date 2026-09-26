import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ImageRecord } from "../types";
import { ImageListItem } from "./image-list-item";

const record: ImageRecord = {
  record_id: "b6693c65-1f3f-4169-a741-a9fc2ef1a36b",
  slug: "m31",
  name: "m31",
};

function renderItem(item: ImageRecord) {
  const rootRoute = createRootRoute({
    component: () => (
      <>
        <ImageListItem record={item} />
        <Outlet />
      </>
    ),
  });
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/",
    component: () => null,
  });
  const imageRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/image/$recordId/{-$slug}",
    component: () => null,
  });
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute, imageRoute]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  return render(<RouterProvider router={router} />);
}

describe("ImageListItem", () => {
  it("renders record name and truncated id", async () => {
    renderItem(record);

    const item = await screen.findByTestId("image-list-item");
    expect(item).toHaveTextContent("m31");
    expect(item).toHaveTextContent("b6693c65…");
    expect(item).toHaveTextContent("Ver imagen");
    expect(screen.getByTestId("image-list-item-open")).toHaveAttribute(
      "href",
      "/image/b6693c65-1f3f-4169-a741-a9fc2ef1a36b/m31",
    );
  });

  it("shows the download filename when it differs from the object name", async () => {
    renderItem({ ...record, slug: "hst_123.fits" });

    expect(await screen.findByTestId("image-list-item-slug")).toHaveTextContent(
      "hst_123.fits",
    );
    expect(screen.getByTestId("image-list-item-open")).toHaveAttribute(
      "href",
      "/image/b6693c65-1f3f-4169-a741-a9fc2ef1a36b/hst_123.fits",
    );
  });
});
