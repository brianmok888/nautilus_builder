import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Default: at root, no tab
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@ant-design/icons", () => ({
  AppstoreOutlined: () => <span>AppstoreIcon</span>,
  BarChartOutlined: () => <span>BarchartIcon</span>,
  CodeOutlined: () => <span>CodeIcon</span>,
  ExperimentOutlined: () => <span>ExperimentIcon</span>,
  FileTextOutlined: () => <span>FiletextIcon</span>,
  PlayCircleOutlined: () => <span>PlayIcon</span>,
  SafetyCertificateOutlined: () => <span>SafetyIcon</span>,
  SettingOutlined: () => <span>SettingIcon</span>,
  ThunderboltOutlined: () => <span>ThunderIcon</span>,
}));

import { BuilderSidebar } from "./BuilderSidebar";

describe("BuilderSidebar", () => {
  it("renders the brand title", () => {
    render(<BuilderSidebar />);
    expect(screen.getByText("Nautilus Builder")).toBeTruthy();
    expect(screen.getByText("Strategy workspace")).toBeTruthy();
  });

  it("renders all navigation items", () => {
    render(<BuilderSidebar />);
    expect(screen.getByText("Overview")).toBeTruthy();
    expect(screen.getByText("Strategy Builder")).toBeTruthy();
    expect(screen.getByText("Backtest Center")).toBeTruthy();
    expect(screen.getByText("Execution Lane")).toBeTruthy();
    expect(screen.getByText("Strategy Specs")).toBeTruthy();
    expect(screen.getByText("Pipeline")).toBeTruthy();
    expect(screen.getByText("Results")).toBeTruthy();
    expect(screen.getByText("Settings")).toBeTruthy();
  });

  it("highlights the active route (Overview at root with no tab)", () => {
    const { container } = render(<BuilderSidebar />);
    const activeLink = container.querySelector(".nb-sidebar-link-active");
    expect(activeLink).toBeTruthy();
    expect(activeLink?.textContent).toContain("Overview");
  });

  it("uses clean path routes for root dashboard lanes", () => {
    render(<BuilderSidebar />);

    const strategyLink = screen.getByText("Strategy Builder").closest("a");
    const backtestLink = screen.getByText("Backtest Center").closest("a");
    const executionLink = screen.getByText("Execution Lane").closest("a");

    expect(strategyLink?.getAttribute("href")).toBe("/builder");
    expect(backtestLink?.getAttribute("href")).toBe("/backtests");
    expect(executionLink?.getAttribute("href")).toBe("/execution");
  });

  it("shows Builder-only mode footer", () => {
    render(<BuilderSidebar />);
    expect(screen.getByText(/Builder-only mode/)).toBeTruthy();
    expect(screen.getByText(/No live orders/)).toBeTruthy();
  });
});
