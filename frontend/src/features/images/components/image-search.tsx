import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";

type ImageSearchProps = {
  value: string;
  onSearch: (query: string) => void;
};

export function ImageSearch({ value, onSearch }: ImageSearchProps) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    const handle = setTimeout(() => {
      if (local !== value) {
        onSearch(local);
      }
    }, 300);
    return () => clearTimeout(handle);
  }, [local, value, onSearch]);

  return (
    <Input
      type="search"
      placeholder="Search by object name, e.g. M31, Orion…"
      value={local}
      onChange={(e) => setLocal(e.target.value)}
      className="mx-auto max-w-lg"
      aria-label="Search images"
    />
  );
}
