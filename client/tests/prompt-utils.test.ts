import { describe, expect, it } from "vitest";

import { inputToTextList, previewFromBlocks, textListToInput } from "../src/shared/utils/prompt";
import type { PromptBlocks } from "../src/shared/types/api";

const blocks: PromptBlocks = {
  intent: "premium editorial product photography",
  subject: "croissant and coffee",
  action_state: "",
  environment: "quiet hotel breakfast table",
  composition: "negative space",
  camera_lens: "85mm",
  lighting: "soft morning window light",
  material_texture: "linen and ceramic",
  color_palette: "warm ivory",
  style: "commercial finish",
  text_in_image: ["Menu"],
  positive_constraints: "no visible person",
  notes: "internal note"
};

describe("prompt utils", () => {
  it("converts comma-separated text image labels", () => {
    expect(inputToTextList("Menu, Cafe,  ")).toEqual(["Menu", "Cafe"]);
    expect(textListToInput(["Menu", "Cafe"])).toBe("Menu, Cafe");
  });

  it("builds preview without notes", () => {
    const preview = previewFromBlocks(blocks);
    expect(preview).toContain("croissant and coffee");
    expect(preview).not.toContain("internal note");
  });
});
