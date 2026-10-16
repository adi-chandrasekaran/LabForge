import { expect, test, type Page } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8017";
const apiBase = `http://127.0.0.1:${backendPort}/api/v1`;

async function mockNmrFoundation(page: Page) {
  await page.route(`${apiBase}/nmr/imports`, route => route.fulfill({ json: [] }));
  await page.route(`${apiBase}/nmr/proteins`, route => route.fulfill({ json: [{ id: "protein-1", name: "ANC2", construct_name: "ANC2", sequence: "M", isotope_labels: ["15N"], residue_count: 1 }] }));
  await page.route(`${apiBase}/nmr/samples`, route => route.fulfill({ json: [] }));
  await page.route(`${apiBase}/nmr/ligands`, route => route.fulfill({ json: [] }));
  await page.route(`${apiBase}/nmr/residues?protein_id=*`, route => route.fulfill({ json: [{ id: "residue-1", protein_id: "protein-1", sequence_number: 1, insertion_code: "", residue_name: "MET", one_letter_code: "M", notes: "" }] }));
}

test("a successful provider retest immediately enables the assistant", async ({ page }) => {
  await page.route(`${apiBase}/agent/status`, route => route.fulfill({ json: {
    available: false, code: "ollama_unavailable", provider: "ollama", model: "llama3.2", detail: "Ollama is not reachable.",
  } }));
  await page.route(`${apiBase}/agent/provider-diagnostic`, route => route.fulfill({ json: {
    ok: true, provider: "ollama", model: "llama3.2", code: null,
    detail: "Ollama and model 'llama3.2' completed a live response test.", state: "ready", action: null,
  } }));

  await page.goto("/assistant");
  const ask = page.getByRole("button", { name: "Ask assistant" });
  await page.getByPlaceholder("Ask a question about your NMR data", { exact: false }).fill("List my spectra");
  await expect(ask).toBeDisabled();

  await page.getByRole("button", { name: "Test provider connection" }).click();

  await expect(page.getByText("Provider ready")).toBeVisible();
  await expect(page.getByText("ollama · ready")).toBeVisible();
  await expect(ask).toBeEnabled();
});

test("NMR explorer reports detail failures instead of claiming data is empty", async ({ page }) => {
  await mockNmrFoundation(page);
  await page.route(`${apiBase}/nmr/spectra`, route => route.fulfill({ json: [{ id: "spectrum-1", name: "ANC2 HSQC", sample_id: null, experiment_type: "1H-15N HSQC", nuclei: ["1H", "15N"], status: "processed", peak_count: 1 }] }));
  await page.route(`${apiBase}/nmr/peaks?spectrum_id=*`, route => route.fulfill({ status: 500, json: { detail: "Peak service temporarily failed" } }));
  await page.route(`${apiBase}/nmr/chemical-shifts?spectrum_id=*`, route => route.fulfill({ json: [] }));

  await page.goto("/nmr-data");

  await expect(page.getByRole("alert")).toContainText("Peak service temporarily failed");
  await expect(page.getByText("No peaks stored.")).not.toBeVisible();
});

test("changing analysis mode clears stale results and explains empty matches", async ({ page }) => {
  await mockNmrFoundation(page);
  const spectra = [
    { id: "spectrum-1", name: "Reference", sample_id: null, experiment_type: "HSQC", nuclei: ["1H", "15N"], status: "processed", peak_count: 0 },
    { id: "spectrum-2", name: "Comparison", sample_id: null, experiment_type: "HSQC", nuclei: ["1H", "15N"], status: "processed", peak_count: 0 },
  ];
  await page.route(`${apiBase}/nmr/spectra`, route => route.fulfill({ json: spectra }));
  await page.route(`${apiBase}/nmr/peaks?spectrum_id=*`, route => route.fulfill({ json: [] }));
  await page.route(`${apiBase}/nmr/chemical-shifts?spectrum_id=*`, route => route.fulfill({ json: [] }));
  await page.route(`${apiBase}/nmr/analyses/compare-spectra`, route => route.fulfill({ json: {
    reference_spectrum_id: "spectrum-1", comparison_spectrum_id: "spectrum-2",
    matched_shift_count: 0, reference_only_count: 0, comparison_only_count: 0, deltas: [],
  } }));

  await page.goto("/nmr-data");
  await page.getByRole("button", { name: "Analyze shifts" }).click();
  await page.getByRole("button", { name: "Compare spectra" }).click();
  await expect(page.getByText("No chemical shifts matched between these spectra.")).toBeVisible();

  await page.getByRole("button", { name: "CSP" }).click();
  await expect(page.getByText("No chemical shifts matched between these spectra.")).not.toBeVisible();
});

