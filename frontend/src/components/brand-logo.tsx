import { useId } from "react";
import { cn } from "@/lib/utils";

type BrandLogoProps = {
  className?: string;
};

export function BrandLogo({ className }: Readonly<BrandLogoProps>) {
  const maskId = `corte-hex-${useId().replaceAll(":", "")}`;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 100 100"
      aria-labelledby={`${maskId}-title`}
      className={cn("text-foreground", className)}
    >
      <title id={`${maskId}-title`}>astroimage</title>
      <defs>
        <mask id={maskId}>
          <rect width="100%" height="100%" fill="white" />
          <polygon
            points="55,25 75,37 75,63 55,75 35,63 35,37"
            fill="none"
            stroke="black"
            strokeWidth="6"
          />
        </mask>
      </defs>
      <polygon
        points="45,25 65,37 65,63 45,75 25,63 25,37"
        fill="none"
        className="stroke-foreground"
        strokeWidth="4"
        mask={`url(#${maskId})`}
      />
      <polygon
        points="50,42 56,46 56,54 50,58 44,54 44,46"
        className="fill-primary"
      />
      <polygon
        points="55,25 75,37 75,63 55,75 35,63 35,37"
        fill="none"
        className="stroke-primary"
        strokeWidth="4"
      />
    </svg>
  );
}
