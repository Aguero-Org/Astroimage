# ADR 0002: Onboarding desacoplado de los componentes de negocio

- Estado: aceptado
- Fecha: 2026-11-16
- Alcance: `frontend/src/features/onboarding`

## Contexto

Queremos un onboarding: una serie de pasos que expliquen las pantallas a quien entra por primera vez. Dos condiciones fijan la forma.

Los componentes de negocio no deben conocer la existencia del onboarding. Si un componente de `features/images` importa un paso de tour o recibe una prop para marcar su posición, cada cambio de producto arrastra al onboarding y cada limpieza del onboarding toca negocio.

El onboarding reutiliza los tokens visuales y las primitivas existentes (`frontend/src/index.css`, `components/ui`). La app ya marca los controles con `data-testid`, que es el ancla disponible.

## Alternativas

| Alternativa | Encaje con React | Cuánto se reimplementa | Accesibilidad y posicionamiento |
| --- | --- | --- | --- |
| Motor propio (selector, geometría y portal) | Correcto | Overlay, spotlight, posicionamiento, foco y teclado | Hay que resolverlos a mano |
| react-joyride v3 | React-first, `steps` declarativo, hook | Nada del tour; solo el tooltip para vestirlo con tokens | Incluye foco, ARIA y posicionamiento con Floating UI |
| driver.js | Agnóstico, control imperativo | El wiring React | Incluye foco, ARIA y posicionamiento |
| reactour | React-first, paquetes mask/popover/tour | Nada del tour | Incluye ambos; soporte de React 19 menos claro |

## Decisión

react-joyride v3 para el motor, con una capa propia mínima en `frontend/src/features/onboarding` montada en el shell (`routes/__root.tsx`), que ya aloja la UI transversal.

- Un tour es data pura (`tours.ts`): `{ id, route, label, steps }`. Cada paso es un `Step` de Joyride (`target`, `title`, `content`, `placement`). `target` es un selector CSS que apunta a un `data-testid` existente.
- Joyride es dueño del overlay, el spotlight, el posicionamiento (Floating UI) y el foco/teclado. No se reimplementa nada de eso.
- El tooltip se viste con un `tooltipComponent` propio (`components/onboarding-tooltip.tsx`) que usa los tokens (`bg-popover`, `text-popover-foreground`, `border-border`) y `Button`.
- La selección es por ruta. `tourForRoute` (en `tours.ts`) devuelve el tour de la sección actual. Hoy hay tres: `primeros-pasos` (`/`), `visor` (`/image`) y `glosario` (`/glossary`).
- El estado vive en un store Zustand (`onboarding-store.ts`): tour activo y tours completados. Solo los completados se persisten en `localStorage`. El launcher (`OnboardingLauncher`) arranca el tour de la ruta y `autoStartTourId` es el arranque automático opcional. El negocio no llama al onboarding en ningún punto.

Agregar un tour es agregar una entrada en `tours.ts`; no se toca ningún componente de negocio.

## Consecuencias

- El ancla es el selector. Un `data-testid` renombrado rompe el paso que lo usa; Joyride espera el objetivo (`targetWaitTimeout`) y, si no aparece, la app sigue funcionando.
- El tooltip del tour lo posiciona Floating UI (vía Joyride). Los popovers de la app los sigue posicionando Radix. Son dos instancias distintas de "posicionar un popover": Radix para la app, Joyride para el tour.
- Cada tour cubre una sola ruta. Un recorrido que salte de la búsqueda al visor necesita que el paso declare su ruta y que la capa navegue antes.
- `react-joyride` agrega Floating UI y utilidades propias; queda en el allowed stack de la skill `react-spa`.
