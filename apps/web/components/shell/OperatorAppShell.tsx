"use client";

import { ErrorBoundary } from "./ErrorBoundary";
import { useHealthCheck } from "../../hooks/useHealthCheck";

import {
  ApiOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Badge, ConfigProvider, Layout, Menu, Space, Tag, theme, Typography } from "antd";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const navigationItems = [
  {
    key: "/",
    icon: <RobotOutlined />,
    label: <a href="/">Strategy Builder</a>,
  },
  {
    key: "/backtests",
    icon: <ExperimentOutlined />,
    label: <a href="/backtests">Backtest Center</a>,
  },
  {
    key: "/execution",
    icon: <PlayCircleOutlined />,
    label: <a href="/execution">Execution Lane</a>,
  },
  {
    key: "/config",
    icon: <SettingOutlined />,
    label: <a href="/config">Config</a>,
  },
  {
    key: "/strategies",
    icon: <FileTextOutlined />,
    label: <a href="/strategies">Strategy records</a>,
  },
  {
    key: "/results/res_001",
    icon: <BarChartOutlined />,
    label: <a href="/results/res_001">Results / Reports</a>,
  },
];

function selectedNavigationKey(pathname: string) {
  if (pathname.startsWith("/strategies")) return "/strategies";
  if (pathname.startsWith("/config")) return "/config";
  if (pathname.startsWith("/execution")) return "/execution";
  if (pathname.startsWith("/backtests")) return "/backtests";
  if (pathname.startsWith("/results")) return "/results/res_001";
  return "/";
}

function HealthIndicator() {
  const health = useHealthCheck();
  const color = health.status === "healthy" ? "success" : health.status === "degraded" ? "warning" : "error";
  const label = health.status === "healthy" ? "API healthy" : health.status === "degraded" ? "API degraded" : "API down";
  return <Tag color={color}>{label}{health.latencyMs != null ? ` (${health.latencyMs}ms)` : ""}</Tag>;
}

export function OperatorAppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const selectedKey = selectedNavigationKey(pathname);

  return (
    <ConfigProvider
      componentSize="small"
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#38bdf8",
          colorSuccess: "#34d399",
          colorWarning: "#fbbf24",
          colorBgBase: "#07111f",
          colorBgContainer: "#101827",
          colorBorder: "rgba(148, 163, 184, 0.24)",
          borderRadius: 10,
          controlHeight: 30,
          fontSize: 13,
          lineHeight: 1.35,
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
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
              <Typography.Text type="secondary">AI → Backtest → Execution</Typography.Text>
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
          <Layout.Content className="operator-content"><ErrorBoundary>{children}</ErrorBoundary></Layout.Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}
