import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BacktestLaunchPanel } from "./BacktestLaunchPanel";

describe("BacktestLaunchPanel layout", () => {
  afterEach(() => vi.restoreAllMocks());

  it("uses the manifest grid layout for run manifest fields", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<BacktestLaunchPanel />);

    const grid = document.querySelector(".manifest-form-grid");
    expect(grid).toBeInTheDocument();

    const fields = document.querySelectorAll(".manifest-form-field");
    expect(fields.length).toBeGreaterThanOrEqual(6);
  });

  it("applies hash-field class on compile hash input", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<BacktestLaunchPanel />);

    const hashInput = document.querySelector(".hash-field");
    expect(hashInput).toBeInTheDocument();
  });

  it("renders manifest preview with manifest-preview class", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<BacktestLaunchPanel />);

    const preview = document.querySelector(".manifest-preview");
    expect(preview).toBeInTheDocument();
  });

  it("uses manifest-section blocks for run manifest and preview", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<BacktestLaunchPanel />);

    const sections = document.querySelectorAll(".manifest-section");
    expect(sections.length).toBeGreaterThanOrEqual(2);
  });

  it("preserves evidence-only safety copy with authority metadata", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<BacktestLaunchPanel />);

    expect(screen.getByText(/may_submit_order: false/i)).toBeInTheDocument();
    expect(screen.getByText(/manual promotion after review/i)).toBeInTheDocument();
    expect(screen.getByText(/Backtest launch is evidence-only/i)).toBeInTheDocument();
  });

  it("does not contain forbidden live trading wording", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<BacktestLaunchPanel />);
    const body = document.body.textContent ?? "";
    expect(body).not.toMatch(/start live trading/i);
    expect(body).not.toMatch(/auto trade now/i);
    expect(body).not.toMatch(/live bot running/i);
    expect(body).not.toMatch(/guaranteed profit/i);
    expect(body).not.toMatch(/deploy to exchange/i);
    expect(body).not.toMatch(/execute strategy/i);
  });
});
