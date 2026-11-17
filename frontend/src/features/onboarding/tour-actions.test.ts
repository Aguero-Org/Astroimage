import { afterEach, describe, expect, it, vi } from "vitest";
import {
  focusScientificTab,
  openInspector,
  openScientific,
  selectFirstSource,
} from "./tour-actions";

const cleanups: Array<() => void> = [];

function mountButton(
  testId: string,
  expanded?: boolean,
): { onClick: () => void } {
  const button = document.createElement("button");
  button.setAttribute("data-testid", testId);
  if (expanded !== undefined) {
    button.setAttribute("aria-expanded", String(expanded));
  }
  const onClick = vi.fn(() => {
    if (expanded !== undefined) {
      button.setAttribute("aria-expanded", "true");
    }
  });
  button.addEventListener("click", onClick);
  document.body.append(button);
  cleanups.push(() => button.remove());
  return { onClick };
}

function mountMarker(testId: string): { remove: () => void } {
  const element = document.createElement("span");
  element.setAttribute("data-testid", testId);
  document.body.append(element);
  cleanups.push(() => element.remove());
  return { remove: () => element.remove() };
}

afterEach(() => {
  for (const cleanup of cleanups.splice(0)) {
    cleanup();
  }
});

describe("tour-actions", () => {
  it("opens the inspector when it is closed", async () => {
    const { onClick } = mountButton("inspector-toggle", false);
    await openInspector();
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("leaves an open inspector alone", async () => {
    const { onClick } = mountButton("inspector-toggle", true);
    await openInspector();
    expect(onClick).not.toHaveBeenCalled();
  });

  it("opens the scientific panel when it is closed", async () => {
    const { onClick } = mountButton("scientific-toggle", false);
    await openScientific();
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("resolves when the toggle is absent", async () => {
    await expect(openInspector()).resolves.toBeUndefined();
  });

  it("opens the scientific panel and focuses a tab", async () => {
    const toggle = mountButton("scientific-toggle", false);
    const tab = mountButton("scientific-tab-papers");
    await focusScientificTab("scientific-tab-papers");
    expect(toggle.onClick).toHaveBeenCalledTimes(1);
    expect(tab.onClick).toHaveBeenCalledTimes(1);
  });

  it("selects the first source when none is selected", async () => {
    const marker = mountButton("source-marker");
    await selectFirstSource();
    expect(marker.onClick).toHaveBeenCalledTimes(1);
  });

  it("keeps the current selection", async () => {
    mountMarker("source-selection");
    const marker = mountButton("source-marker");
    await selectFirstSource();
    expect(marker.onClick).not.toHaveBeenCalled();
  });
});
