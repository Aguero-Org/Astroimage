import { useEffect } from "react";

export function useDocumentTitle(title: string, fallback: string) {
  useEffect(() => {
    document.title = title;
    return () => {
      document.title = fallback;
    };
  }, [title, fallback]);
}
