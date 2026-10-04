# Web UI design guidelines

This reference distills the workshop "Diseño estético de apps web" into agent-usable design heuristics. It is intentionally framework-agnostic.

## 0. Context and user

- Identify the target audience before making interface decisions.
- A user persona can help make consistent decisions about needs and expectations.
- Consider device, usage context, language, and writing direction.
- Do not assume Western reading conventions for every audience; Arabic and Hebrew interfaces may require reversed visual ordering.

## 1. Information architecture and navigation

### Scanning and hierarchy

Users commonly scan pages rather than reading them linearly. Use a visual hierarchy that makes points of interest and primary actions easy to find.

Common Western scan patterns include F-shaped scanning for text-heavy pages and Z-shaped scanning for simpler compositions. Treat these as observations, not templates.

On mobile, prioritize important actions where they are comfortable to reach with the thumb and treat the layout primarily as a vertical flow.

### Navigation

- Side navigation is generally appropriate when there are many options.
- A top bar is generally appropriate when there are few primary options or when navigation should use the full width.
- Collapse side navigation when space requires it.
- Keep top navigation sticky when persistent access is important.
- Group related navigation items logically.
- Avoid treating the "three clicks" rule as a universal requirement.

### Wayfinding

Use appropriate combinations of:

- Active navigation state.
- Page title.
- Breadcrumbs for hierarchical locations.

The goal is for users to understand both where they are and how the current location relates to the rest of the application.

## 2. Structure and consistency

### Spacing

An 8px-based spacing scale is a useful default. Consistency matters more than rigid adherence to a particular scale.

### Design tokens

Prefer semantic tokens such as:

- `color-bg-primary`
- `color-bg-secondary`
- `color-fg-primary`

Map semantic roles to palette values for themes such as light and dark mode. Avoid coupling components directly to raw palette values when a semantic role exists.

### Styling boundaries

Keep global component styles reusable. Page-specific styling should be scoped and as small as possible.

### Grid and responsive layout

A 12-column grid is a common mental model because it divides cleanly into 6, 4, 3, and 2 columns. It is not a strict implementation requirement.

Responsive design should change the composition when necessary. For example, three desktop cards occupying four columns each may become three full-width blocks on mobile.

## 3. Information density

Density depends on the product:

- Landing pages generally benefit from generous space.
- Repeated productivity applications may use standard or compact density.
- Dashboards prioritize decision-relevant information and can reduce prose.
- Applications used continuously for many hours should avoid excessively small or overlapping text.

Whitespace is structural: it groups, separates, and establishes hierarchy.

## 4. Interaction design

### Affordances and signifiers

- Interactive elements must look interactive.
- Links should be visually recognizable as links.
- Icons should have recognizable meanings and consistent usage.
- Do not depend on users learning an arbitrary icon vocabulary.

### Feedback

- Provide hover/interaction feedback where appropriate.
- When an action is unavailable, communicating the disabled/unavailable state can be preferable to hiding it.
- Slow operations need visible progress feedback.
- Use skeleton loading when the eventual structure can be represented before content arrives.
- Use success feedback such as a toast when appropriate.

### Errors

- Prefer progressive feedback over disruptive interruption.
- Do not unnecessarily interrupt data entry.
- Destructive actions should be confirmed when accidental activation has meaningful consequences.
- Error messages should explain the problem and how to resolve it when possible.

## 5. Forms and data entry

Data entry is cognitively expensive. Optimize forms for comprehension and completion.

### Layout

- Prefer single-column forms for ordinary data entry.
- Group fields by theme.
- Split long forms into meaningful steps and communicate the current step.
- Keep labels visible instead of relying on disappearing placeholders.
- Explain difficult validation rules before users submit invalid data.
- Labels above controls are especially appropriate on mobile.
- For one-column desktop forms, labels may be placed to the left when this improves scanning; account for writing direction and locale.

### Control selection

Use the closed option-set size and semantics as the starting point:

| Options | Typical control |
| --- | --- |
| 2–4 mutually exclusive | Radio group |
| 5+ mutually exclusive | Dropdown/select |
| Multiple selection, up to roughly 5–6 | Checkboxes |
| Larger multiple-selection sets | Multi-select dropdown |
| Immediate binary state change | Switch |
| Binary choice confirmed by form submission | Checkbox |
| Approximate/relative numeric value | Slider |
| Precise date input | Date picker plus manual entry |
| Large or dynamic list | Autocomplete |

These are heuristics. Dynamic or frequently changing lists can justify a select/autocomplete even when the current number of options is small.

### Interaction details

- Larger and closer targets are generally faster to operate (Fitts' law).
- Validation commonly works well on blur for individual fields.
- Error feedback should tell users how to fix the value.
- Do not disable the primary submit action solely as a way to communicate invalidity when doing so harms discoverability or accessibility.
- Autofocus the first input only when it does not interfere with navigation or accessibility.
- Enter-to-submit can be useful when consistent with the form's semantics and product expectations.
- Masks can help with dates, numbers, and phone numbers when they reduce entry errors.
- Autocomplete for large/dynamic lists should avoid excessive requests; debounce remote queries.

## 6. Typography

- 16px is a useful starting point for body text.
- Choose font personality according to the product. For example, Inter can communicate a modern neutral UI, JetBrains-style type can reinforce a technical character, and a serif such as Instrument Serif can communicate warmth or editorial character.
- Font combinations should establish contrast without reducing readability.
- Typography should create hierarchy, attract attention where useful, and avoid confusion.

## 7. Color

A practical palette often contains:

- Primary/accent color.
- Secondary color.
- Base/neutral color.

A 60-30-10 distribution can be used as an indicative starting heuristic (roughly 60% base, 30% secondary, 10% accent), not as a rule.

Use semantic status colors consistently:

- Red: error.
- Yellow: warning/alert.
- Green: success.
- Blue: information.

Do not rely on status color alone to communicate meaning. Labels generally should not be colored merely for decoration; reserve strong color emphasis for meaningful states or links. Grayscale is useful for borders and secondary text.

Contrast must remain sufficient for the intended text and UI.

## 8. Icons

Icons can reduce the learning curve when their meaning is recognizable. Avoid decorative icons that add noise. Keep icon style and semantics consistent across the application.

## 9. Accessibility

Use WCAG as the accessibility reference and organize checks around POUR:

### Perceivable

- Provide text alternatives for non-text content.
- Provide captions/transcripts when applicable.
- Maintain at least 4.5:1 contrast for normal text as the baseline cited by the source material.

### Operable

- Do not require one specific input mechanism.
- Provide alternative navigation mechanisms where appropriate.
- Allow users to pause or obtain more time when content expires or auto-advances.

### Understandable

- Keep behavior predictable.
- Provide meaningful labels and understandable messages.
- Avoid unexpected changes of context.

### Robust

- Build against broadly supported web platform behavior.
- Consider browsers, screen readers, and mobile interaction environments.

Useful automated checks include Lighthouse, WAVE, and axe DevTools.

## Source boundary

This reference preserves the workshop's heuristics rather than turning them into absolute laws. When a project has stronger product, accessibility, platform, or user research constraints, those constraints should drive the final decision.
