import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock useHealthCheck
vi.mock("../../hooks/useHealthCheck", () => ({
  useHealthCheck: () => ({ status: "healthy", latencyMs: 12, error: null }),
}));

// Mock antd icons (returns simple spans)
vi.mock("@ant-design/icons", () => ({
  AppstoreOutlined: () => <span data-testid="icon-appstore" />,
  BarChartOutlined: () => <span data-testid="icon-barchart" />,
  CodeOutlined: () => <span data-testid="icon-code" />,
  ExperimentOutlined: () => <span data-testid="icon-experiment" />,
  FileTextOutlined: () => <span data-testid="icon-filetext" />,
  PlayCircleOutlined: () => <span data-testid="icon-play" />,
  SafetyCertificateOutlined: () => <span data-testid="icon-safety" />,
  SettingOutlined: () => <span data-testid="icon-setting" />,
  ThunderboltOutlined: () => <span data-testid="icon-thunder" />,
  ApiOutlined: () => <span data-testid="icon-api" />,
}));

import { BuilderShell } from "./BuilderShell";

describe("BuilderShell", () => {
  it("renders the light app shell", () => {
    const { container } = render(
      <BuilderShell>
        <p>Page content</p>
      </BuilderShell>,
    );

    // Has the nb-app-shell class (light shell)
    expect(container.querySelector(".nb-app-shell")).toBeTruthy();
    // Has the nb-sidebar
    expect(container.querySelector(".nb-sidebar")).toBeTruthy();
    // Shows page content
    expect(screen.getByText("Page content")).toBeTruthy();
  });

  it("shows BuilderSafetyBanner text", () => {
    render(
      <BuilderShell>
        <p>Test</p>
      </BuilderShell>,
    );

    expect(screen.getByText("Builder-only mode")).toBeTruthy();
    expect(
      screen.getByText(/does not submit live orders/i),
    ).toBeTruthy();
  });

  it("shows the health indicator", () => {
    render(
      <BuilderShell>
        <p>Test</p>
      </BuilderShell>,
    );

    expect(screen.getByText(/API healthy/)).toBeTruthy();
  });

  it("renders the top bar with API base label", () => {
    render(
      <BuilderShell>
        <p>Test</p>
      </BuilderShell>,
    );

    expect(screen.getByText("server-side API base")).toBeTruthy();
  });
});
