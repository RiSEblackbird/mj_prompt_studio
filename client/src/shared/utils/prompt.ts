import type { PromptBlocks } from "../types/api";

export const blockLabels: Record<keyof PromptBlocks, string> = {
  intent: "Intent",
  subject: "Subject",
  action_state: "Action / State",
  environment: "Environment",
  composition: "Composition",
  camera_lens: "Camera / Lens",
  lighting: "Lighting",
  material_texture: "Material / Texture",
  color_palette: "Color Palette",
  style: "Style",
  text_in_image: "Text in Image",
  positive_constraints: "Positive Constraints",
  notes: "Notes"
};

export const blockOrder: (keyof PromptBlocks)[] = [
  "intent",
  "subject",
  "action_state",
  "environment",
  "composition",
  "camera_lens",
  "lighting",
  "material_texture",
  "color_palette",
  "style",
  "text_in_image",
  "positive_constraints",
  "notes"
];

export function textListToInput(items: string[]): string {
  return items.join(", ");
}

export function inputToTextList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function previewFromBlocks(blocks: PromptBlocks): string {
  return blockOrder
    .filter((field) => field !== "notes")
    .flatMap((field) => {
      const value = blocks[field];
      return Array.isArray(value) ? value : [value];
    })
    .map((value) => value.trim())
    .filter(Boolean)
    .join(", ");
}
