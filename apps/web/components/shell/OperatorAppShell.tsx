"use client";

import { ErrorBoundary } from "./ErrorBoundary";
import { useHealthCheck } from "../../hooks/useHealthCheck";

import {
  ApiOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { Badge, ConfigProvider, Layout, Menu, Space, Tag, Typography, theme } from "antd";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, type ReactNode } from "react";

const navigationItems = [
  {
    key: "/",
    icon: <PlayCircleOutlined />,
    label: <Link href="/">Overview</Link>,
  },
  {
    key: "/?tab=strategy",
    icon: <ExperimentOutlined />,
    label: <Link href="/?tab=strategy">Strategy Builder</Link>,
  },
  {
    key: "/?tab=backtest",
    icon: <ExperimentOutlined />,
    label: <Link href="/?tab=backtest">Backtest Center</Link>,
  },
  {
    key: "/?tab=execution",
    icon: <PlayCircleOutlined />,
    label: <Link href="/?tab=execution">Execution Lane</Link>,
  },
  {
    key: "/strategies",
    icon: <FileTextOutlined />,
    label: <Link href="/strategies">Strategy Specs</Link>,
  },
  {
    key: "/pipeline",
    icon: <ThunderboltOutlined />,
    label: <Link href="/pipeline">Pipeline</Link>,
  },
  {
    key: "/results",
    icon: <BarChartOutlined />,
    label: <Link href="/results">Results</Link>,
  },
  {
    key: "/config",
    icon: <SettingOutlined />,
    label: <Link href="/config">Settings</Link>,
  },
];

function selectedNavigationKey(pathname: string, tab: string | null) {
  if (pathname.startsWith("/strategies")) return "/strategies";
  if (pathname.startsWith("/config")) return "/config";
  if (pathname.startsWith("/pipeline")) return "/pipeline";
  if (pathname.startsWith("/results")) return "/results";
  if (pathname === "/" && tab === "backtest") return "/?tab=backtest";
  if (pathname === "/" && tab === "execution") return "/?tab=execution";
  if (pathname === "/" && tab === "strategy") return "/?tab=strategy";
  if (pathname === "/") return "/";
  return pathname;
}

function HealthIndicator() {
  const health = useHealthCheck();
  const color =
    health.status === "healthy"
      ? "success"
      : health.status === "degraded"
        ? "warning"
        : "error";
  const label =
    health.status === "healthy"
      ? "API healthy"
      : health.status === "degraded"
        ? "API degraded"
        : "API down";
  return (
    <Tag color={color}>
      {label}
      {health.latencyMs != null ? ` (${health.latencyMs}ms)` : ""}
    </Tag>
  );
}

function ShellContent({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const tab = searchParams.get("tab");
  const selectedKey = selectedNavigationKey(pathname, tab);

  return (
    <ConfigProvider
      componentSize="small"
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1d9bf0",
          colorSuccess: "#22c55e",
          colorWarning: "#f59e0b",
          colorBgBase: "#f5f7fb",
          colorBgContainer: "#ffffff",
          colorBorder: "#edf0f5",
          borderRadius: 14,
          controlHeight: 34,
          fontSize: 13,
          lineHeight: 1.35,
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        },
        components: {
          Menu: {
            itemBorderRadius: 12,
            itemSelectedBg: "#eaf7ff",
            itemSelectedColor: "#1d9bf0",
            itemHoverBg: "#f4f8fc",
          },
          Card: {
            borderRadiusLG: 18,
          },
          Button: {
            borderRadius: 12,
          },
        },
      }}
    >
      <Layout className="operator-shell">
        <Layout.Sider
          breakpoint="lg"
          collapsedWidth={0}
          className="operator-sider"
          width={260}
        >
          <div className="operator-brand" aria-label="Nautilus Builder brand">
            <div className="operator-brand-mark">NB</div>
            <div>
              <div className="operator-brand-title">Nautilus Builder</div>
              <Typography.Text type="secondary">
                AI → Backtest → Execution
              </Typography.Text>
            </div>
          </div>
          <nav aria-label="Operator workflow" className="operator-nav-menu">
            <Menu
              mode="inline"
              items={navigationItems}
              selectedKeys={[selectedKey]}
              className="operator-menu"
            />
          </nav>
          <div className="operator-safety-card">
            <Space direction="vertical" size={8}>
              <Tag color="success" icon={<SafetyCertificateOutlined />}>
                Builder-only
              </Tag>
              <Typography.Text>No live order authority</Typography.Text>
              <Typography.Text type="secondary">
                Validation, backtest evidence, and manual promotion gates remain
                backend-owned.
              </Typography.Text>
            </Space>
          </div>
        </Layout.Sider>
        <Layout className="operator-main-layout">
          <Layout.Header className="operator-header">
            <Space wrap className="operator-header-left">
              <Badge status="processing" text="FastAPI / worker contracts" />
              <Tag color="blue" icon={<ApiOutlined />}>
                server-side API base
              </Tag>
            </Space>
            <Space wrap>
              <HealthIndicator />
            </Space>
          </Layout.Header>
          <Layout.Content className="operator-content">
            <ErrorBoundary>{children}</ErrorBoundary>
          </Layout.Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export function OperatorAppShell({ children }: { children: ReactNode }) {
  return (
    <Suspense>
      <ShellContent>{children}</ShellContent>
    </Suspense>
  );
}
