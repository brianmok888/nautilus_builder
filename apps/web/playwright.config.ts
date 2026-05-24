import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://127.0.0.1:3000",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command:
      "bash -lc 'cd ../..; python3 -m services.api.dev_server --host 127.0.0.1 --port 8000 & API_PID=$!; trap \"kill $API_PID 2>/dev/null || true\" EXIT; cd apps/web; next dev --hostname 127.0.0.1 --port 3000'",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: false,
  },
});
