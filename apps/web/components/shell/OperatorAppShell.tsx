"use client";

/**
 * @deprecated Use BuilderShell instead.
 * OperatorAppShell is kept as a re-export for backwards compatibility
 * with existing tests and E2E specs that reference this name.
 */
import { BuilderShell } from "./BuilderShell";
import type { ReactNode } from "react";

export function OperatorAppShell({ children }: { children: ReactNode }) {
  return <BuilderShell>{children}</BuilderShell>;
}
