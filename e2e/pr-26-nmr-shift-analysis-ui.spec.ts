import { expect, test } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8017";
const apiBase = `http://127.0.0.1:${backendPort}/api/v1`;

test("researcher compares spectra and calculates CSP from stored shifts", async ({ page, request }) => {
  const protein = await (await request.post(`${apiBase}/nmr/proteins`, { data: { name: "Analysis protein", sequence: "M" } })).json() as { id: string };
  const residue = await (await request.post(`${apiBase}/nmr/residues`, { data: { protein_id: protein.id, sequence_number: 1, residue_name: "MET", one_letter_code: "M" } })).json() as { id: string };
  const sample = await (await request.post(`${apiBase}/nmr/samples`, { data: { name: "Analysis sample", protein_ids: [protein.id] } })).json() as { id: string };
  const reference = await (await request.post(`${apiBase}/nmr/spectra`, { data: { name: "Analysis reference", sample_id: sample.id, nuclei: ["1H", "15N"] } })).json() as { id: string };
  const comparison = await (await request.post(`${apiBase}/nmr/spectra`, { data: { name: "Analysis bound", sample_id: sample.id, nuclei: ["1H", "15N"] } })).json() as { id: string };
  for (const [spectrumId, h, n] of [[reference.id, 8.0, 120.0], [comparison.id, 8.1, 121.0]] as const) {
    await request.post(`${apiBase}/nmr/chemical-shifts`, { data: { spectrum_id: spectrumId, residue_id: residue.id, atom_name: "H", nucleus: "1H", value_ppm: h } });
    await request.post(`${apiBase}/nmr/chemical-shifts`, { data: { spectrum_id: spectrumId, residue_id: residue.id, atom_name: "N", nucleus: "15N", value_ppm: n } });
  }

  await page.goto("/nmr-data");
  await page.getByRole("button", { name: "Analyze shifts" }).click();
  await page.getByLabel("Reference spectrum").selectOption(reference.id);
  await page.getByLabel("Comparison spectrum").selectOption(comparison.id);
  await page.getByRole("button", { name: "Compare spectra" }).click();
  const comparisonResult = page.getByTestId("spectrum-comparison-result");
  await expect(comparisonResult).toContainText("Matched shifts");
  await expect(comparisonResult).toContainText("0.100");
  await expect(comparisonResult).toContainText("1.000");

  await page.getByRole("button", { name: "CSP", exact: true }).click();
  await page.getByRole("button", { name: "Calculate CSP" }).click();
  const cspResult = page.getByTestId("csp-result");
  await expect(cspResult).toContainText("1 matched residues");
  await expect(cspResult).toContainText("0.1836");
  await expect(cspResult).toContainText("sqrt(sum((nucleus_weight * delta_ppm)^2))");
});
