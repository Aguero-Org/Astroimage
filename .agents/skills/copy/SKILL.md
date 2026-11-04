---
name: copy
description: >-
  Writing rule for prose a person reads in astroimage: placeholders, labels,
  HelpHint, toasts, empty states, errors, glossary, README, and docs/entrega.
  Use when writing or reviewing that prose, or when checking it for AI tells
  (not-X-but-Y, closers, aphorisms, inflated significance, system narration).
---

# Copy

State the fact or the constraint. Do not stage it.

A model writes the sentence that fits the widest reader. That shows up as
structure, not as a banned word. Word lists rot. These shapes do not.

Source: Wikipedia, [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
and the structural list in [Humanizer](https://github.com/blader/humanizer).
Do not install that skill. Do not tune text to fool a detector.

## How to apply

1. Read the whole passage. Mark tells, strongest first.
2. Rewrite around the fact. Do not patch one flagged phrase and leave the
   staging around it.
3. Keep every supported claim. Do not invent a name, number, or limit.
4. Read it again for the tells that survive a rewrite: contrasts, closers,
   triads, and "Permite…".

Act on one sighting of §1–§5. The rest count when several share a passage.
Leave a phrase alone inside a quotation, a title, or a sentence that
discusses the phrase. A real contrast stays when both halves tell the
reader something they need.

## Strong

1. **Not X, but Y.** `no es X, es Y`, `no es un error`, `no solo X sino Y`,
   `simplemente`, `más que X, es Y`. State the fact.
2. **Closer.** A last line that repeats the point (`en definitiva`,
   `esa es la diferencia`). Cut it.
3. **Aphorism.** `en el fondo`, `lo que realmente importa`, `puerta de
   entrada`, `reduciendo la distancia`. Replace it with the specific claim.
4. **Run-up.** `a continuación`, `veamos`, `cabe destacar`. Start at the
   point.
5. **Arguing with no one.** A denial of a reading the reader did not make.
   Drop the denial. Keep the fact that was hiding behind it.

## Rhythm and inflation

6. **Triad for rhythm.** Three items because three sounds complete. Keep
   three only when there are three facts.
7. **Inflated significance.** `nace para`, `a futuro`, `pivotal`,
   `clave para`, `barrera importante`, `enorme cantidad`. Keep the fact.
   End on the last concrete sentence.
8. **Sales language.** `accesible`, `intuitivo`, `visual e intuitiva` used
   as praise. Say what the person can do.
9. **Avoiding "es".** `nace para`, `busca conectar`, `se convierte en`,
   `Permite…` as a section opener. Use `es` or name the action.
10. **Shallow rider.** A gerund bolted on to add weight (`reduciendo…`,
    `empezando por…`, `así que`). Keep the clause only when it adds a fact.
11. **System narration.** `el servidor guarda`, `la API`, `el diagrama se
    realiza`. Say what the user gets or what failed. A stored file living
    on the server is a fact. Narrating the mechanism is not.

## Weak alone

Dashes, passive voice in a delivery report, and bold on a filename are
not a tell by themselves. A page full of them, plus a closer, is.

Do not flag: empty-value `—`, a range (`0–100`), a command, a path, or
a preset hint that states a real limit (`No si lo que buscás es ese fondo`).

## This product

- Placeholder: one valid example. Never an instruction (`Escribí…`,
  `Si lo dejás vacío…`, `Buscar por…`).
- The label stays. The placeholder is not the label.
- HelpHint: the effect in the app, not the implementation. The glossary
  is the longer version of the same meaning, not a second explanation of
  the server.
- Error: what failed and, if known, the limit. Do not list every check.
- Spanish UI uses voseo (`dejá`, `probá`).
- Scope of this rule: strings a person reads. Not code, not tests, not
  this skill, not `AGENTS.md`.
