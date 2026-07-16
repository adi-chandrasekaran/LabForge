import { defineConfig, devices } from '@playwright/test'

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? '8017'
const frontendPort = process.env.PLAYWRIGHT_FRONTEND_PORT ?? '4174'
const backendUrl = `http://127.0.0.1:${backendPort}`
const frontendUrl = `http://127.0.0.1:${frontendPort}`
const frontendApiBase = `${backendUrl}/api/v1`
const skipWebServer = process.env.PLAYWRIGHT_SKIP_WEBSERVER === '1'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: frontendUrl,
    trace: 'retain-on-failure',
  },
  webServer: skipWebServer
    ? undefined
    : [
        {
          command: `.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port ${backendPort}`,
          url: `${backendUrl}/api/v1/health`,
          reuseExistingServer: true,
          timeout: 30_000,
        },
        {
          command: `VITE_API_BASE_URL=${frontendApiBase} npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
          url: frontendUrl,
          reuseExistingServer: true,
          timeout: 30_000,
        },
      ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
