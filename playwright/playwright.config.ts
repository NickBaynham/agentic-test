import { defineConfig } from '@playwright/test';
import path from 'path';

const repoRoot = path.resolve(__dirname, '..');
const port = process.env.PLAYWRIGHT_API_PORT ?? '18080';
const baseURL = process.env.API_BASE_URL ?? `http://127.0.0.1:${port}`;

/** `CI=false` is a common default in shells but is truthy as a string — treat only positive values as CI. */
const isCi = ['1', 'true', 'yes'].includes(String(process.env.CI ?? '').toLowerCase());

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: isCi,
  retries: isCi ? 2 : 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL,
    extraHTTPHeaders: {
      Accept: 'application/json',
    },
  },
  projects: [{ name: 'api' }],
  webServer: process.env.PLAYWRIGHT_SKIP_WEBSERVER
    ? undefined
    : {
        command: `bash "${path.join(repoRoot, 'scripts', 'run-api-for-playwright.sh')}"`,
        cwd: repoRoot,
        env: {
          ...process.env,
          PLAYWRIGHT_API_PORT: port,
        },
        url: `${baseURL}/health`,
        timeout: 120_000,
        reuseExistingServer: !isCi,
      },
});
