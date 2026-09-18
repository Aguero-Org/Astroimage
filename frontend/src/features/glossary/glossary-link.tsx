import { Link } from "@tanstack/react-router";
import { BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

type GlossaryLinkProps = {
  testId: string;
  className?: string;
};

export function GlossaryLink({
  testId,
  className,
}: Readonly<GlossaryLinkProps>) {
  return (
    <Link
      to="/glossary"
      data-testid={testId}
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground",
        className,
      )}
    >
      <BookOpen className="size-4" aria-hidden />
      Glosario
    </Link>
  );
}
