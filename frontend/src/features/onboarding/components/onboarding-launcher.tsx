import { CircleHelp } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useOnboardingStore } from "../onboarding-store";

type OnboardingLauncherProps = {
  tourId?: string;
};

export function OnboardingLauncher({
  tourId,
}: Readonly<OnboardingLauncherProps>) {
  const activeTourId = useOnboardingStore((state) => state.activeTourId);
  const start = useOnboardingStore((state) => state.start);

  if (activeTourId || !tourId) {
    return null;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          data-testid="onboarding-launcher"
          aria-label="Ver recorrido guiado"
          className="fixed right-4 bottom-4 z-40 rounded-full shadow-lg"
          onClick={() => start(tourId)}
        >
          <CircleHelp className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="left">Recorrido guiado</TooltipContent>
    </Tooltip>
  );
}
