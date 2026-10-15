---
name: web-ui-design
description: >-
  Design and review web application interfaces using a user-centered approach
  covering information architecture, navigation, layout consistency, interaction,
  forms, visual UI, and accessibility. Use when designing, implementing,
  reviewing, or improving a web application's interface or user experience.
---

# Web UI design

Use this skill as a cross-cutting design review and decision framework for web application interfaces. It is framework-, library-, and platform-agnostic.

## Workflow

1. **Understand users and context**
   - Identify target users, primary tasks, usage context, devices, language/writing direction, and expected information density.
   - Treat these constraints as inputs to later design decisions rather than assuming a generic audience.

2. **Design information architecture and navigation**
   - Make the current location and the next useful action apparent without requiring users to infer the application's structure.
   - Design for scanning: establish a clear visual hierarchy and prioritize important content/actions according to the reading direction and device.
   - Choose navigation according to option count and product structure: side navigation generally suits many options; top navigation suits a small set of primary options.
   - Group navigation logically and preserve wayfinding with active states, page titles, and breadcrumbs where hierarchy warrants them.
   - Do not apply fixed click-count rules mechanically.

3. **Establish structural consistency**
   - Use a coherent spacing scale; 8px multiples are a useful default.
   - Prefer reusable design tokens and shared components over page-specific styling.
   - Use semantic color tokens/roles rather than scattering raw palette values through components.
   - Keep page-specific styling small and scoped to genuinely local needs.
   - Use a 12-column grid as a responsive mental model when useful; it is not a requirement.
   - Define how content reflows at smaller sizes instead of merely shrinking desktop layouts.

4. **Choose information density deliberately**
   - Match density to the task: exploratory/marketing pages can breathe; repeated professional workflows often need more compact layouts; dashboards should prioritize the information required for decisions.
   - Use whitespace to group, separate, and establish hierarchy.
   - Avoid density that makes text too small, controls difficult to distinguish, or content overlap.

5. **Design interaction and feedback**
   - Every interactive element should have an understandable affordance/signifier.
   - Use consistent visual feedback for interactive states.
   - When an action is unavailable, prefer communicating that state when it helps users understand the interface.
   - Provide feedback for slow operations; use skeleton/progressive loading where the layout can be represented before data arrives.
   - Confirm destructive actions when accidental activation would have meaningful consequences.
   - Report success and errors progressively without unnecessarily interrupting the user's flow.
   - Errors should explain what happened and, when possible, how to fix it.

6. **Design forms for low cognitive effort**
   - Prefer a single-column flow for ordinary data-entry forms.
   - Group related fields and split genuinely long forms into meaningful steps with clear progress.
   - Keep labels visible; do not rely on disappearing placeholders as the primary label.
   - Explain non-obvious rules before or at the point where they matter.
   - Select controls according to the option set and interaction semantics, not personal preference.
   - Make targets sufficiently large and close to the action context.
   - Validate at an appropriate point in the interaction, commonly on blur for individual fields.
   - Avoid making the primary action undiscoverable merely because it is currently invalid.
   - Use useful microinteractions such as appropriate autofocus, keyboard submission, and input masks where they reduce effort without hiding the underlying value.

7. **Establish visual UI**
   - Choose typography for readability and product personality; a 16px base size is a useful default for body text.
   - Use typography to establish hierarchy rather than adding decoration.
   - Define semantic color roles for backgrounds, foregrounds, accents, and status states.
   - Never make color the only carrier of meaning.
   - Use icons when they reduce learning effort or clarify actions; avoid decorative icon noise and inconsistent icon semantics.

8. **Apply accessibility as a quality requirement**
   - Use the POUR principles: perceivable, operable, understandable, robust.
   - Provide text alternatives for non-text content and captions/transcripts where applicable.
   - Maintain sufficient contrast; WCAG's 4.5:1 ratio is the baseline referenced by this skill for normal text.
   - Ensure functionality does not depend on a single input mechanism and remains usable with keyboard/assistive technology.
   - Keep behavior predictable, labels meaningful, and feedback understandable.
   - Consider time limits, auto-advancing content, and mechanisms to pause or obtain more time.
   - Validate with tools such as Lighthouse, WAVE, or axe DevTools when available.

## Decision principles

When heuristics conflict, prioritize in this order:

1. User task and context.
2. Low cognitive effort and clear information hierarchy.
3. Consistency with the application's design system.
4. Clear affordances, states, actions, and feedback.
5. Accessibility and input-method independence.

Treat numeric thresholds and visual heuristics as defaults, not laws. The appropriate choice depends on the product, audience, content, device, and interaction context.

## Review checklist

Before considering a UI design complete, verify:

- Can the target user identify where they are?
- Can they recognize the primary task/action?
- Is important content easy to scan?
- Is navigation grouped and predictable?
- Are layout, spacing, typography, and semantic colors consistent?
- Is information density appropriate for the task?
- Are interactive controls visually recognizable and stateful?
- Do loading, success, unavailable, and error states communicate clearly?
- Do forms minimize cognitive and mechanical effort?
- Are typography, color, and icons serving hierarchy rather than decoration?
- Is the interface usable without relying on color, mouse, or a single input mechanism?
- Has accessibility been checked with an appropriate automated tool and, where practical, manual interaction?

## Reference

For the detailed heuristics and thresholds distilled from the source material, read `references/design-guidelines.md` when the task requires more specific design decisions.
