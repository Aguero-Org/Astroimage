import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { server } from "./server";

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

class ResizeObserverStub {
  observe(): void {
    // jsdom has no layout engine
  }
  unobserve(): void {
    // jsdom has no layout engine
  }
  disconnect(): void {
    // jsdom has no layout engine
  }
}

window.ResizeObserver = ResizeObserverStub;

Element.prototype.hasPointerCapture ??= () => false;
Element.prototype.setPointerCapture ??= () => {};
Element.prototype.releasePointerCapture ??= () => {};
Element.prototype.scrollIntoView ??= () => {};

// Mocks for JSDOM
window.scrollTo = vi.fn();
window.scroll = vi.fn();
window.scrollBy = vi.fn();
