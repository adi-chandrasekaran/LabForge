import { expect, test, type Page } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8017";
const apiBase = `http://127.0.0.1:${backendPort}/api/v1`;

async function openAssistant(page: Page) {
  await page.route(`${apiBase}/agent/status`, async (route) => {
    await route.fulfill({ json: { available: true, provider: "ollama", model: "llama3.2", detail: "Ollama is running and the model is installed." } });
  });
  await page.goto("/assistant");
}

test("reports a successful live Ollama model test", async ({ page }) => {
  await page.route(`${apiBase}/agent/provider-diagnostic`, async (route) => {
    await route.fulfill({ json: {
      ok: true,
      provider: "ollama",
      model: "llama3.2",
      code: null,
      detail: "Ollama and model 'llama3.2' completed a live response test.",
      state: "ready",
      action: null,
    } });
  });
  await openAssistant(page);

  await page.getByRole("button", { name: "Test provider connection" }).click();

  await expect(page.getByText("Provider ready")).toBeVisible();
  await expect(page.getByText("completed a live response test", { exact: false })).toBeVisible();
});

test("explains when Ollama is unavailable", async ({ page }) => {
  await page.route(`${apiBase}/agent/provider-diagnostic`, async (route) => {
    await route.fulfill({ json: {
      ok: false,
      provider: "ollama",
      model: "llama3.2",
      code: "ollama_unavailable",
      detail: "Ollama is not reachable on the configured local address.",
      state: "unavailable",
      action: "Open Ollama, then test the connection again.",
    } });
  });
  await openAssistant(page);

  await page.getByRole("button", { name: "Test provider connection" }).click();

  await expect(page.getByText("Ollama unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("Next step: Open Ollama", { exact: false })).toBeVisible();
  await expect(page.getByText("Diagnostic code: ollama unavailable")).toBeVisible();
});

test("provides the exact pull command when the model is missing", async ({ page }) => {
  await page.route(`${apiBase}/agent/provider-diagnostic`, async (route) => {
    await route.fulfill({ json: {
      ok: false,
      provider: "ollama",
      model: "llama3.2",
      code: "model_unavailable",
      detail: "Ollama is running, but model 'llama3.2' is not installed.",
      state: "model_missing",
      action: "Run: ollama pull llama3.2",
    } });
  });
  await openAssistant(page);

  await page.getByRole("button", { name: "Test provider connection" }).click();

  await expect(page.getByText("Ollama model missing")).toBeVisible();
  await expect(page.getByText("ollama pull llama3.2", { exact: false })).toBeVisible();
});
