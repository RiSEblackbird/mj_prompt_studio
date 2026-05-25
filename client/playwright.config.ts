import { defineConfig, devices } from "@playwright/test";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(dirname, "..");
const e2eDataDir = path.join(repoRoot, ".tmp", `e2e-data-${Date.now()}`);
const localVenvPython = path.join(repoRoot, ".venv", "bin", "python");
const pythonCommand =
  process.env.MJPS_E2E_PYTHON ?? (fs.existsSync(localVenvPython) ? localVenvPython : "python");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "on-first-retry"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: [
    {
      command: `${pythonCommand} -m mj_prompt_studio.server.main`,
      cwd: repoRoot,
      env: {
        MJPS_DATA_DIR: e2eDataDir,
        MJPS_LLM_MODE: "mock"
      },
      url: "http://127.0.0.1:8765/api/health",
      reuseExistingServer: false,
      timeout: 30_000
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
      timeout: 30_000
    }
  ]
});
