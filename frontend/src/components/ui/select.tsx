import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

function Select({
  className,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      data-slot="select"
      className={cn("ui-select", className)}
      {...props}
    >
      {children}
    </select>
  );
}

export { Select };
