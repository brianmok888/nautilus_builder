import { defineConfig } from "vitest/config";

export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  test: {
    exclude: ["**/node_modules/**", "**/dist/**", "**/e2e/**"],
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    testTimeout: 15_000,
  },
});
