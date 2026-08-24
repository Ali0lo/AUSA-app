import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://127.0.0.1:3100";
const managesServer = !process.env.PLAYWRIGHT_TEST_BASE_URL;
const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: executablePath ? { executablePath } : undefined
  },
  webServer: managesServer
    ? {
        command: "npm run dev -- --hostname 127.0.0.1 --port 3100",
        url: baseURL,
        reuseExistingServer: true,
        timeout: 120000,
        env: {
          ...process.env,
          NEXT_PUBLIC_API_URL: `${baseURL}/api/v1`,
          NEXTAUTH_URL: baseURL,
          NEXTAUTH_SECRET: "ausa-browser-test-secret"
        }
      }
    : undefined,
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        permissions: ["clipboard-read", "clipboard-write"]
      }
    }
  ]
});
