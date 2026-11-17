import type { TooltipRenderProps } from "react-joyride";
import { Button } from "@/components/ui/button";

export function OnboardingTooltip({
  index,
  size,
  step,
  backProps,
  primaryProps,
  skipProps,
  tooltipProps,
}: Readonly<TooltipRenderProps>) {
  return (
    <div
      {...tooltipProps}
      data-testid="onboarding-card"
      className="max-w-xs rounded-lg border border-border bg-popover p-4 text-popover-foreground shadow-lg"
    >
      <p
        data-testid="onboarding-progress"
        className="text-xs font-medium text-muted-foreground"
      >
        {index + 1} de {size}
      </p>
      {step.title ? (
        <h2 className="mt-1 text-sm font-semibold">{step.title}</h2>
      ) : null}
      <div className="mt-2 text-sm text-muted-foreground">{step.content}</div>
      <div className="mt-4 flex items-center justify-between gap-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          data-testid="onboarding-skip"
          {...skipProps}
        >
          {skipProps.title}
        </Button>
        <div className="flex items-center gap-2">
          {index > 0 ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              data-testid="onboarding-previous"
              {...backProps}
            >
              {backProps.title}
            </Button>
          ) : null}
          <Button
            type="button"
            size="sm"
            data-testid="onboarding-next"
            {...primaryProps}
          >
            {primaryProps.title}
          </Button>
        </div>
      </div>
    </div>
  );
}
