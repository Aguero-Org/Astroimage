import { useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";

type ScrollSpyOptions = {
  offsetPx?: number;
  fallbackId?: string;
};

function subscribe(onStoreChange: () => void) {
  window.addEventListener("scroll", onStoreChange, { passive: true });
  window.addEventListener("resize", onStoreChange);
  window.addEventListener("astroimage-scroll-spy", onStoreChange);
  return () => {
    window.removeEventListener("scroll", onStoreChange);
    window.removeEventListener("resize", onStoreChange);
    window.removeEventListener("astroimage-scroll-spy", onStoreChange);
  };
}

function preferredId(ids: readonly string[], fallbackId: string): string {
  if (fallbackId.length > 0 && ids.includes(fallbackId)) {
    return fallbackId;
  }
  return ids[0] ?? "";
}

function measureActiveId(
  ids: readonly string[],
  offsetPx: number,
): string | null {
  const lastId = ids[ids.length - 1] ?? "";
  const viewport = window.innerHeight;
  const pageHeight = document.documentElement.scrollHeight;
  const scrolledToEnd =
    pageHeight > viewport + 1 && window.scrollY + viewport >= pageHeight - 2;
  if (scrolledToEnd) {
    return lastId;
  }

  const measured = ids.flatMap((id) => {
    const node = document.getElementById(id);
    if (!node) {
      return [];
    }
    return [{ id, top: node.getBoundingClientRect().top }];
  });
  if (measured.length === 0) {
    return null;
  }
  if (measured.every((item) => item.top === 0)) {
    return null;
  }
  let current = measured[0]?.id ?? "";
  for (const item of measured) {
    if (item.top - offsetPx <= 0) {
      current = item.id;
    }
  }
  return current;
}

export function useScrollSpy(
  ids: readonly string[],
  options: ScrollSpyOptions = {},
): string {
  const offsetPx = options.offsetPx ?? 96;
  const fallbackId = options.fallbackId ?? "";
  const idsKey = ids.join("\0");
  const lastGoodId = useRef("");
  const getSnapshot = () => {
    if (ids.length === 0) {
      return "";
    }
    const measured = measureActiveId(ids, offsetPx);
    if (
      measured === null &&
      lastGoodId.current.length > 0 &&
      ids.includes(lastGoodId.current)
    ) {
      return lastGoodId.current;
    }
    const next = measured ?? preferredId(ids, fallbackId);
    lastGoodId.current = next;
    return next;
  };
  const activeId = useSyncExternalStore(subscribe, getSnapshot, () =>
    preferredId(ids, fallbackId),
  );

  useLayoutEffect(() => {
    window.dispatchEvent(
      new CustomEvent("astroimage-scroll-spy", {
        detail: `${idsKey}:${offsetPx}:${fallbackId}`,
      }),
    );
  }, [idsKey, offsetPx, fallbackId]);

  return activeId;
}

export function useStickyStackHeight(testIds: readonly string[]): number {
  const [height, setHeight] = useState(0);

  useLayoutEffect(() => {
    const measure = () => {
      setHeight(
        testIds.reduce((sum, testId) => {
          const node = document.querySelector(`[data-testid="${testId}"]`);
          return sum + (node?.getBoundingClientRect().height ?? 0);
        }, 0),
      );
    };
    measure();
    window.addEventListener("resize", measure);
    return () => {
      window.removeEventListener("resize", measure);
    };
  }, [testIds]);

  return height;
}
