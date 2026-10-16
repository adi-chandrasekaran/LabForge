import { expect, test, type Page } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8017";
const apiBase = `http://127.0.0.1:${backendPort}/api/v1`;

const completedRun = {
  id: "agent-run-1",
  user_request: "What shifts are stored for residue M1?",
  status: "completed",
  final_answer: "M1 has a stored 1H shift of 8.12 ppm.",
  data_availability: "retrieved",
  failure_code: null,
  failure_detail: null,
  tool_calls: [
    {
      id: "agent-tool-call-1",
      sequence: 1,
      tool_name: "get_residue_shifts",
      arguments: { residue_id: "residue-m1" },
      result: { tool_name: "get_residue_shifts", ok: true, data: [{ nucleus: "1H", value_ppm: 8.12 }], error: null },
      status: "completed",
      error_message: null,
    },
  ],
};

async function mockReadyProvider(page: Page) {
  await page.route(`${apiBase}/agent/status`, async (route) => {
    await route.fulfill({
      json: { available: true, provider: "ollama", model: "llama3.2", detail: "Ollama is ready." },
    });
  });
}

test("restores the latest conversation and its ordered evidence audit", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("nmr-lab-agent-conversation-id", "agent-conversation-1"));
  await mockReadyProvider(page);
  await page.route(`${apiBase}/agent/conversations/agent-conversation-1/runs`, async (route) => {
    await route.fulfill({ json: [{ ...completedRun, tool_calls: undefined }] });
  });
  await page.route(`${apiBase}/agent/conversations/agent-conversation-1/runs/agent-run-1`, async (route) => {
    await route.fulfill({ json: completedRun });
  });

  await page.goto("/assistant");

  await expect(page.getByText("M1 has a stored 1H shift of 8.12 ppm.")).toBeVisible();
  await page.getByText("Evidence and tool audit (1)").click();
  await expect(page.getByText("get_residue_shifts", { exact: false })).toBeVisible();

  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(page.getByText("Try an evidence-backed NMR question:")).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.localStorage.getItem("nmr-lab-agent-conversation-id"))).toBeNull();
});

test("creates and remembers a conversation while explaining active retrieval", async ({ page }) => {
  await mockReadyProvider(page);
  await page.route(`${apiBase}/agent/conversations`, async (route) => {
    await route.fulfill({ status: 201, json: { id: "agent-conversation-new", title: "NMR research assistant" } });
  });
  await page.route(`${apiBase}/agent/conversations/agent-conversation-new/runs`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 250));
    await route.fulfill({ status: 201, json: completedRun });
  });

  await page.goto("/assistant");
  await page.getByPlaceholder("Ask a question about your NMR data", { exact: false }).fill(completedRun.user_request);
  await page.getByRole("button", { name: "Ask assistant" }).click();

  await expect(page.getByText("Retrieving evidence and running tools…")).toBeVisible();
  await expect(page.getByText(completedRun.final_answer)).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.localStorage.getItem("nmr-lab-agent-conversation-id"))).toBe("agent-conversation-new");
});

test("shows structured provider failures as readable text", async ({ page }) => {
  await mockReadyProvider(page);
  await page.route(`${apiBase}/agent/conversations`, async (route) => {
    await route.fulfill({ status: 201, json: { id: "agent-conversation-failed" } });
  });
  await page.route(`${apiBase}/agent/conversations/agent-conversation-failed/runs`, async (route) => {
    await route.fulfill({
      status: 502,
      contentType: "application/json",
      body: JSON.stringify({ code: "provider_failed", message: "Ollama could not complete the request." }),
    });
  });

  await page.goto("/assistant");
  await page.getByPlaceholder("Ask a question about your NMR data", { exact: false }).fill("List my spectra");
  await page.getByRole("button", { name: "Ask assistant" }).click();

  await expect(page.getByRole("alert")).toContainText("Ollama could not complete the request. (provider failed)");
  await expect(page.getByRole("alert")).not.toContainText('{"code"');
});
