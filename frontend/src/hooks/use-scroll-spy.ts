import { useEffect, useLayoutEffect, useState } from "react";

type ScrollSpyOptions = {
  offsetPx?: number;
  fallbackId?: string;
};

export function useScrollSpy(
  ids: readonly string[],
  options: ScrollSpyOptions = {},
): string {
  const offsetPx = options.offsetPx ?? 96;
  const fallbackId = options.fallbackId ?? "";
  const [activeId, setActiveId] = useState(
    fallbackId.length > 0 && ids.includes(fallbackId)
      ? fallbackId
      : (ids[0] ?? ""),
  );

  useEffect(() => {
    setActiveId((current) => {
      if (current.length > 0 && ids.includes(current)) {
        return current;
      }
      if (fallbackId.length > 0 && ids.includes(fallbackId)) {
        return fallbackId;
      }
      return ids[0] ?? "";
    });
  }, [ids, fallbackId]);

  useEffect(() => {
    if (ids.length === 0) {
      return;
    }

    const update = () => {
      const lastId = ids[ids.length - 1] ?? "";
      const viewport = window.innerHeight;
      const pageHeight = document.documentElement.scrollHeight;
      const scrolledToEnd =
        pageHeight > viewport + 1 &&
        window.scrollY + viewport >= pageHeight - 2;
      if (scrolledToEnd) {
        setActiveId(lastId);
        return;
      }

      const measured = ids.flatMap((id) => {
        const node = document.getElementById(id);
        if (!node) {
          return [];
        }
        return [{ id, top: node.getBoundingClientRect().top }];
      });
      if (measured.length === 0) {
        return;
      }
      if (measured.every((item) => item.top === 0)) {
        return;
      }
      let current = measured[0]?.id ?? "";
      for (const item of measured) {
        if (item.top - offsetPx <= 0) {
          current = item.id;
        }
      }
      setActiveId(current);
    };

    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [ids, offsetPx]);

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
