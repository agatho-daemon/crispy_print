import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PdfPreviewRenderer from "../../components/PdfPreviewRenderer.vue";
import { decodePdfData } from "../../utils/pdfBytes";

const mocks = vi.hoisted(() => {
  const render = vi.fn((_pageNumber: number) => ({
    promise: Promise.resolve(),
    cancel: vi.fn(),
  }));
  const destroyDocument = vi.fn(() => Promise.resolve());
  const destroyLoading = vi.fn(() => Promise.resolve());
  const getTextContent = vi.fn(async () => ({
    items: [
      {
        str: "Selectable report text",
        dir: "ltr",
        transform: [],
        width: 1,
        height: 1,
        fontName: "f1",
      },
    ],
    styles: {},
  }));
  const getPage = vi.fn(async (number: number) => ({
    getViewport: ({ scale }: { scale: number }) => ({
      width: 800,
      height: 1100,
      scale,
    }),
    render: () => render(number),
    getTextContent,
  }));
  const renderTextLayer = vi.fn();
  const cancelTextLayer = vi.fn();
  const TextLayer = vi.fn(
    ({ container }: { container: HTMLElement }) => ({
      render: async () => {
        renderTextLayer(container);
        const span = document.createElement("span");
        span.textContent = "Selectable report text";
        container.append(span);
      },
      cancel: cancelTextLayer,
    }),
  );
  const getDocument = vi.fn(() => ({
    promise: Promise.resolve({
      numPages: 20,
      getPage,
      destroy: destroyDocument,
    }),
    destroy: destroyLoading,
  }));
  return {
    render,
    renderTextLayer,
    cancelTextLayer,
    TextLayer,
    getTextContent,
    destroyDocument,
    destroyLoading,
    getPage,
    getDocument,
  };
});

vi.mock("../../utils/pdfJs", () => ({
  loadPdfJs: async () => ({
    GlobalWorkerOptions: {},
    getDocument: mocks.getDocument,
    TextLayer: mocks.TextLayer,
  }),
}));

let observerCallback: IntersectionObserverCallback | null = null;

class ObserverStub {
  observe = vi.fn();
  disconnect = vi.fn();
  constructor(callback: IntersectionObserverCallback) {
    observerCallback = callback;
  }
}

describe("PDF preview renderer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    observerCallback = null;
    (globalThis as any).IntersectionObserver = ObserverStub;
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
      {} as any,
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("decodes report PDF data at the boundary", () => {
    expect(Array.from(decodePdfData("JVBERg=="))).toEqual([37, 80, 68, 70]);
    expect(decodePdfData("").byteLength).toBe(0);
  });

  it("creates placeholders for all pages and keeps painting bounded to the viewport", async () => {
    const scrollRoot = document.createElement("div");
    const wrapper = mount(PdfPreviewRenderer, {
      props: {
        data: new Uint8Array([37, 80, 68, 70]),
        revision: 1,
        viewportRoot: scrollRoot,
      },
    });
    await flushPromises();

    expect(wrapper.findAll(".pdf-preview__page")).toHaveLength(20);
    expect(mocks.render).toHaveBeenCalledTimes(1);
    expect(mocks.render).toHaveBeenCalledWith(1);
    expect(mocks.getTextContent).toHaveBeenCalledWith({
      includeMarkedContent: true,
    });
    expect(wrapper.find(".pdf-preview__text-layer").text()).toBe(
      "Selectable report text",
    );
    expect(
      wrapper
        .find<HTMLElement>(".pdf-preview__text-layer")
        .element.style.getPropertyValue("--scale-factor"),
    ).toBe(String(96 / 72));
    expect(wrapper.emitted("ready")).toBeUndefined();
    expect(wrapper.emitted("state")?.some(([state]) => state === "ready")).toBe(
      true,
    );

    const pageElements = wrapper.findAll<HTMLElement>(".pdf-preview__page");
    observerCallback?.(
      pageElements.map(
        (page) =>
          ({
            target: page.element,
            isIntersecting: true,
          }) as unknown as IntersectionObserverEntry,
      ),
      {} as IntersectionObserver,
    );
    await flushPromises();
    expect(mocks.render.mock.calls.length).toBeLessThanOrEqual(5);

    const firstCanvas = wrapper.find<HTMLCanvasElement>("canvas").element;
    expect(firstCanvas.width).toBeGreaterThan(0);
    expect(wrapper.findAll<HTMLCanvasElement>("canvas")[10].element.width).toBe(
      0,
    );
    observerCallback?.(
      pageElements.map(
        (page, index) =>
          ({
            target: page.element,
            isIntersecting: index === pageElements.length - 1,
          }) as unknown as IntersectionObserverEntry,
      ),
      {} as IntersectionObserver,
    );
    expect(firstCanvas.width).toBe(0);
    expect(wrapper.find(".pdf-preview__text-layer").text()).toBe("");

    wrapper.unmount();
    await flushPromises();
    expect(mocks.destroyLoading).toHaveBeenCalled();
    expect(mocks.destroyDocument).not.toHaveBeenCalled();
  });
});
