"use client";

import type { ReactNode } from "react";
import { BuilderShell } from "../../components/shell/BuilderShell";

export default function BuilderGroupLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <BuilderShell>{children}</BuilderShell>;
}
