import { expect, test } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8017";
const apiBase = `http://127.0.0.1:${backendPort}/api/v1`;

test("researcher browses linked protein and spectrum records", async ({ page, request }) => {
  const protein = await (await request.post(`${apiBase}/nmr/proteins`, { data: { name: "Explorer ANC2", construct_name: "ANC2 1-120", sequence: "M" } })).json() as { id: string };
  const residue = await (await request.post(`${apiBase}/nmr/residues`, { data: { protein_id: protein.id, sequence_number: 1, residue_name: "MET", one_letter_code: "M" } })).json() as { id: string };
  const sample = await (await request.post(`${apiBase}/nmr/samples`, { data: { name: "Explorer sample", protein_ids: [protein.id] } })).json() as { id: string };
  const spectrum = await (await request.post(`${apiBase}/nmr/spectra`, { data: { name: "Explorer HSQC", sample_id: sample.id, experiment_type: "1H-15N HSQC", nuclei: ["1H", "15N"] } })).json() as { id: string };
  const peak = await (await request.post(`${apiBase}/nmr/peaks`, { data: { spectrum_id: spectrum.id, label: "M1", positions_ppm: [8.12, 121.4] } })).json() as { id: string };
  await request.post(`${apiBase}/nmr/assignments`, { data: { peak_id: peak.id, residue_id: residue.id, atom_names: ["H", "N"], status: "confirmed" } });
  await request.post(`${apiBase}/nmr/chemical-shifts`, { data: { spectrum_id: spectrum.id, residue_id: residue.id, peak_id: peak.id, atom_name: "H", nucleus: "1H", value_ppm: 8.12 } });

  await page.goto("/nmr-data");
  const explorer = page.getByTestId("nmr-data-explorer");
  await expect(explorer).toContainText("Explorer ANC2");
  await page.getByRole("button", { name: /Explorer ANC2/ }).click();
  await expect(explorer).toContainText("M1");
  await page.getByLabel("Select spectrum").selectOption(spectrum.id);
  await expect(explorer).toContainText("8.120 / 121.400 ppm");
  await page.getByRole("button", { name: /M1/ }).click();
  await expect(explorer).toContainText("H / N");
  await expect(explorer).toContainText("8.120");
});
