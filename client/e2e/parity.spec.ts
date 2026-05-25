import { expect, test } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const pngBase64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAIAAADN5B7xAAAAGUlEQVR4nGP8z8AARLJgwi1GqGkY1TAAAM6pAqzH/2GfAAAAAElFTkSuQmCC";

test("core local workflow parity", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("banner").getByText("Hotel Breakfast Campaign")).toBeVisible();

  await page.getByLabel("AI Brief").fill("高級ホテルの朝食広告");
  await page.getByRole("button", { name: /AI Brief から構造化/ }).click();
  await expect(page.getByRole("textbox", { name: "Intent" })).toHaveValue(/premium editorial/);

  await page
    .getByRole("textbox", { name: "Subject" })
    .fill("croissant and coffee on refined tableware");
  await page.getByRole("button", { name: /Compile/ }).click();
  await expect(page.getByLabel("Compiled Prompt")).toContainText("croissant and coffee");

  await page.getByRole("button", { name: "Run Prompt Doctor" }).click();
  await expect(page.getByText(/構図の比較軸/)).toBeVisible();
  await page.getByText(/構図の比較軸/).click();
  await page.getByRole("button", { name: "適用" }).click();
  await expect(page.getByRole("textbox", { name: "Composition" })).toHaveValue(
    /close-to-medium/
  );

  await page.getByRole("button", { name: /AI advice/i }).click();
  await expect(page.getByText(/Precision Balanced|Exploration Balanced/)).toBeVisible();
  await page.getByRole("button", { name: "適用" }).click();
  await expect(page.getByText("Parameter Advisor 提案を適用しました")).toBeVisible();

  await page.getByRole("button", { name: "Free Editor" }).click();
  await page.getByLabel("Japanese Source").fill("高級感のある朝食");
  await page.getByRole("button", { name: /英語Prompt化/ }).click();
  await expect(page.getByLabel("Transform Result")).toHaveValue(/premium editorial/);

  const imagePath = writeImage("reference.png");
  await page.getByRole("button", { name: "Reference Library" }).click();
  await page.getByLabel("Reference Library").locator('input[type="file"]').setInputFiles(imagePath);
  await expect(page.getByRole("button", { name: "Analyze reference" })).toBeVisible();
  await page.getByRole("button", { name: "Analyze reference" }).click();
  await expect(page.getByText("soft morning window light")).toBeVisible();
  await page.getByText("soft morning window light").click();
  await page.getByRole("button", { name: "適用" }).click();
  await page.getByRole("button", { name: "Composer" }).click();
  await expect(page.getByRole("textbox", { name: "Style" })).toHaveValue(
    /soft morning window light/
  );

  await page.getByRole("button", { name: "Matrix Lab" }).click();
  await page.getByLabel("Objective").fill("スタイルと構図の比較");
  await page.getByRole("button", { name: /AI Plan/ }).click();
  await expect(page.getByText("stylize")).toBeVisible();
  await page.getByRole("button", { name: /Generate/ }).click();
  await expect(page.getByRole("cell", { name: /--s/ }).first()).toBeVisible();
  await page.getByRole("button", { name: /All/ }).click();
  await page.getByRole("button", { name: "閉じる" }).click();
  await page.getByRole("button", { name: /CSV/ }).click();
  await page.getByRole("button", { name: "閉じる" }).click();
  await page.getByRole("button", { name: /Markdown/ }).click();
  await page.getByRole("button", { name: "閉じる" }).click();

  await page.getByRole("button", { name: "Result Review" }).click();
  await page.getByLabel("Result Review").locator('input[type="file"]').setInputFiles(imagePath);
  await expect(page.getByText(/Source Prompt/)).toBeVisible();
  await page.getByRole("button", { name: /AI Review/ }).click();
  await expect(page.getByText(/全体に高品質/)).toBeVisible();
  await page.getByRole("button", { name: /Next Prompt/ }).click();
  await page.getByRole("button", { name: "適用" }).click();
  await page.getByRole("button", { name: "Result Review" }).click();
  await page.getByRole("button", { name: /Final Audit/ }).click();
  await expect(page.getByText(/コピー前の最終監査/)).toBeVisible();

  await page.getByLabel("Main tabs").getByRole("button", { name: "Settings" }).click();
  const privacyMode = page.getByLabel("Settings").getByLabel("Privacy mode");
  await privacyMode.setChecked(true);
  await expect(page.getByText("Privacy 設定を保存しました")).toBeVisible();
  await expect(privacyMode).toBeChecked();
  await page.reload();
  await page.getByLabel("Main tabs").getByRole("button", { name: "Settings" }).click();
  await expect(page.getByLabel("Settings").getByLabel("Privacy mode")).toBeChecked();
});

function writeImage(filename: string): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "mjps-e2e-"));
  const imagePath = path.join(dir, filename);
  fs.writeFileSync(imagePath, Buffer.from(pngBase64, "base64"));
  return imagePath;
}
