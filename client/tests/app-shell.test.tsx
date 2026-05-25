import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/app/App";

vi.mock("../src/shared/api/client", () => ({
  ApiClientError: class ApiClientError extends Error {},
  api: {
    workspace: vi.fn(() => new Promise(() => undefined)),
    jobs: vi.fn(() => Promise.resolve({ jobs: [] }))
  }
}));

describe("App shell", () => {
  it("shows the product name while loading workspace", () => {
    render(<App />);
    expect(screen.getByText("MJ Prompt Studio")).toBeInTheDocument();
  });
});
