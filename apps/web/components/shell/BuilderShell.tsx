"use client";

import { Suspense, type ReactNode } from "react";
import { BuilderSidebar } from "./BuilderSidebar";
import { BuilderSafetyBanner } from "./BuilderSafetyBanner";
import { BuilderTopBar } from "./BuilderTopBar";
import { ErrorBoundary } from "./ErrorBoundary";

type BuilderShellProps = {
  children: ReactNode;
};

export function BuilderShell({ children }: BuilderShellProps) {
  return (
    <div className="nb-app-shell">
      <Suspense>
        <BuilderSidebar />
      </Suspense>
      <div className="nb-main-wrapper">
        <BuilderTopBar />
        <main className="nb-main">
          <BuilderSafetyBanner />
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
