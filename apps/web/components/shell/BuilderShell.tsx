"use client";

import { Suspense, type ReactNode } from "react";
import { BuilderSidebar } from "./BuilderSidebar";
import { BuilderSafetyBanner } from "./BuilderSafetyBanner";
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
      <main className="nb-main">
        <BuilderSafetyBanner />
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    </div>
  );
}
