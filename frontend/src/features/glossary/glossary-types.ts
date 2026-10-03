export const GLOSSARY_GROUPS = [
  { id: "imagen", title: "Imagen y archivo" },
  { id: "vista", title: "Cómo se ve la imagen" },
  { id: "fuentes", title: "Fuentes" },
  { id: "visor", title: "Uso del visor" },
] as const;

export type GlossaryGroupId = (typeof GLOSSARY_GROUPS)[number]["id"];

export type GlossaryEntry = {
  id: string;
  name: string;
  group: GlossaryGroupId;
  what: string;
  inApp: string;
  where: string;
};
