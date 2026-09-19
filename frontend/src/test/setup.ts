import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => cleanup());

Object.defineProperty(Element.prototype, "scrollIntoView", {
  configurable: true,
  value: vi.fn()
});

if (typeof window !== "undefined") {
  class MockIntersectionObserver {
    observe = vi.fn((target: Element) => {
      // Simulate immediate intersection in tests
      if (this.callback) {
        this.callback([{ isIntersecting: true, target } as unknown as IntersectionObserverEntry], this as unknown as IntersectionObserver);
      }
    });
    unobserve = vi.fn();
    disconnect = vi.fn();
    callback: IntersectionObserverCallback;
    constructor(callback: IntersectionObserverCallback) {
      this.callback = callback;
    }
  }

  Object.defineProperty(window, "IntersectionObserver", {
    configurable: true,
    writable: true,
    value: MockIntersectionObserver
  });
}
