"use client";

import { ConfigProvider, theme } from "antd";
import type { ReactNode } from "react";

type BuilderThemeProviderProps = {
  children: ReactNode;
};

export function BuilderThemeProvider({ children }: BuilderThemeProviderProps) {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1d9bf0",
          colorBgLayout: "#f5f7fb",
          colorBgContainer: "#ffffff",
          colorText: "#1f2937",
          colorTextSecondary: "#8a94a6",
          colorBorder: "#edf0f5",
          borderRadius: 14,
          boxShadowSecondary: "0 12px 32px rgba(15, 23, 42, 0.06)",
          controlHeight: 38,
          fontSize: 13.5,
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        },
        components: {
          Button: {
            borderRadius: 12,
            controlHeight: 38,
          },
          Card: {
            borderRadiusLG: 18,
            paddingLG: 20,
          },
          Table: {
            borderColor: "#edf0f5",
            headerBg: "#f8fafc",
            headerColor: "#334155",
          },
          Menu: {
            itemBorderRadius: 12,
            itemSelectedBg: "#eaf7ff",
            itemSelectedColor: "#1d9bf0",
            itemHoverBg: "#f4f8fc",
          },
          Input: {
            borderRadius: 12,
            controlHeight: 38,
          },
          Select: {
            borderRadius: 12,
            controlHeight: 38,
          },
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
