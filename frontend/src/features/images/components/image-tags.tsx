import { Tag } from "lucide-react";
import type { ReactNode } from "react";

const TAG_TONES = [
  "bg-primary/25 text-primary",
  "bg-accent text-accent-foreground",
  "bg-secondary text-secondary-foreground",
  "bg-muted text-foreground",
  "bg-ring/30 text-foreground",
] as const;

export const tagChipClass =
  "inline-flex h-5 items-center rounded-full border border-border px-2 text-xs font-medium leading-none";

export function tagTone(label: string): string {
  let hash = 0;
  for (const char of label) {
    hash = (hash + char.charCodeAt(0)) % TAG_TONES.length;
  }
  return TAG_TONES[hash] ?? TAG_TONES[0];
}

export function TagChip({
  label,
  children,
}: Readonly<{ label: string; children?: ReactNode }>) {
  return (
    <span className={`${tagChipClass} gap-1 ${tagTone(label)}`}>
      <Tag className="size-3 shrink-0" aria-hidden />
      {label}
      {children}
    </span>
  );
}

export function ImageTags({ tags }: Readonly<{ tags: string[] }>) {
  return (
    <ul className="flex h-5 min-w-0 flex-nowrap items-center gap-1 overflow-hidden">
      {tags.map((label) => (
        <li key={label} className="shrink-0">
          <TagChip label={label} />
        </li>
      ))}
    </ul>
  );
}
