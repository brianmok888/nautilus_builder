"use client";

import {
  AppstoreOutlined,
  BarChartOutlined,
  CodeOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = {
  href: string;
  label: string;
  icon: ReactNode;
  exact?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Overview", icon: <AppstoreOutlined />, exact: true },
  { href: "/builder", label: "Strategy Builder", icon: <CodeOutlined /> },
  { href: "/backtests", label: "Backtest Center", icon: <ExperimentOutlined /> },
  { href: "/execution", label: "Execution Lane", icon: <PlayCircleOutlined /> },
  { href: "/strategies", label: "Strategy Specs", icon: <FileTextOutlined /> },
  { href: "/pipeline", label: "Pipeline", icon: <ThunderboltOutlined /> },
  { href: "/results", label: "Results", icon: <BarChartOutlined /> },
  { href: "/config", label: "Settings", icon: <SettingOutlined /> },
];

function isActive(pathname: string, item: NavItem): boolean {
  if (item.exact) {
    return pathname === item.href;
  }
  return pathname.startsWith(item.href) && item.href !== "/";
}

export function BuilderSidebar() {
  const pathname = usePathname();

  return (
    <aside className="nb-sidebar" aria-label="Nautilus Builder navigation">
      <div className="nb-sidebar-brand">
        <div className="nb-sidebar-logo">NB</div>
        <div>
          <div className="nb-sidebar-title">Nautilus Builder</div>
          <div className="nb-sidebar-subtitle">Strategy workspace</div>
        </div>
      </div>

      <nav className="nb-sidebar-nav" aria-label="Nautilus Builder navigation">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={
                active
                  ? "nb-sidebar-link nb-sidebar-link-active"
                  : "nb-sidebar-link"
              }
            >
              <span className="nb-sidebar-link-icon">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="nb-sidebar-footer">
        <SafetyCertificateOutlined style={{ marginRight: 4 }} />
        Builder-only mode &middot; No live orders
      </div>
    </aside>
  );
}
