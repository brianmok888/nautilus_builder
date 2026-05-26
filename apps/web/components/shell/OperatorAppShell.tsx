"use client";

import {
  ApiOutlined,
  BarChartOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Badge, ConfigProvider, Layout, Menu, Space, Tag, theme, Typography } from "antd";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

const navigationItems = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: <span>Builder dashboard</span>,
  },
  {
    key: "/strategies",
    icon: <FileTextOutlined />,
    label: <span>Strategies</span>,
  },
  {
    key: "/config",
    icon: <SettingOutlined />,
    label: <span>Config</span>,
  },
  {
    key: "/backtests/bt_job_001",
    icon: <ExperimentOutlined />,
    label: <span>Backtest job bt_job_001</span>,
  },
  {
    key: "/results/res_001",
    icon: <BarChartOutlined />,
    label: <span>Results res_001</span>,
  },
];

function selectedNavigationKey(pathname: string) {
  if (pathname.startsWith("/strategies")) return "/strategies";
  if (pathname.startsWith("/config")) return "/config";
  if (pathname.startsWith("/backtests")) return "/backtests/bt_job_001";
  if (pathname.startsWith("/results")) return "/results/res_001";
  return "/";
}

export function OperatorAppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const selectedKey = selectedNavigationKey(pathname);

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#38bdf8",
          colorSuccess: "#34d399",
          colorWarning: "#fbbf24",
          colorBgBase: "#07111f",
          colorBgContainer: "#101827",
          colorBorder: "rgba(148, 163, 184, 0.24)",
          borderRadius: 14,
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
          width={280}
        >
          <div className="operator-brand" aria-label="Nautilus Builder brand">
            <div className="operator-brand-mark">NB</div>
            <div>
              <div className="operator-brand-title">Nautilus Builder</div>
              <Typography.Text type="secondary">StrategySpec console</Typography.Text>
            </div>
          </div>
          <nav aria-label="Operator workflow" className="operator-quick-links">
            <a href="/">Builder dashboard</a>
            <a href="/strategies">Strategies</a>
            <a href="/config">Config</a>
            <a href="/backtests/bt_job_001">Backtest job bt_job_001</a>
            <a href="/results/res_001">Results res_001</a>
          </nav>
          <div aria-label="Operator menu">
            <Menu
              mode="inline"
              items={navigationItems}
              selectedKeys={[selectedKey]}
              className="operator-menu"
              onClick={({ key }) => router.push(key)}
            />
          </div>
          <div className="operator-safety-card">
            <Space orientation="vertical" size={8}>
              <Tag color="success" icon={<SafetyCertificateOutlined />}>
                Advisory-only
              </Tag>
              <Typography.Text>No live order authority</Typography.Text>
              <Typography.Text type="secondary">
                Validation, backtest evidence, and manual promotion gates remain
                backend-owned.
              </Typography.Text>
            </Space>
          </div>
        </Layout.Sider>
        <Layout>
          <Layout.Header className="operator-header">
            <Space wrap className="operator-header-left">
              <Badge status="processing" text="FastAPI proxy monitored" />
              <Tag color="blue" icon={<ApiOutlined />}>
                BUILDER_API_BASE_URL
              </Tag>
            </Space>
            <Space wrap>
              <Tag color="warning">Manual promotion only</Tag>
              <Tag color="default">signal_preview_only</Tag>
            </Space>
          </Layout.Header>
          <Layout.Content className="operator-content">{children}</Layout.Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}
