import { BrandLogo } from "@/components/brand-logo";
import { cn } from "@/lib/utils";

type BrandLoaderProps = {
  label: string;
  className?: string;
  testId?: string;
};

export function BrandLoader({
  label,
  className,
  testId,
}: Readonly<BrandLoaderProps>) {
  return (
    <div
      role="status"
      data-testid={testId}
      className={cn(
        "flex flex-row items-center justify-center gap-3 text-foreground",
        className,
      )}
    >
      <BrandLogo className="size-8 shrink-0 animate-pulse text-foreground" />
      <p className="text-sm text-foreground">{label}</p>
    </div>
  );
}
