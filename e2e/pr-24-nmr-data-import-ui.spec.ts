import { expect, test } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8017";
const apiBase = `http://127.0.0.1:${backendPort}/api/v1`;

test("researcher previews and confirms an NMR residue import", async ({ page, request }) => {
  const proteinResponse = await request.post(`${apiBase}/nmr/proteins`, {
    data: { name: "Import UI protein", sequence: "MA" },
  });
  expect(proteinResponse.ok()).toBeTruthy();
  const protein = await proteinResponse.json() as { id: string };

  await page.goto("/nmr-data");
  await expect(page.getByTestId("nmr-data-title")).toHaveText("NMR data workspace");
  await page.getByRole("button", { name: "Import CSV" }).click();
  await expect(page.getByText("Chemical Shifts", { exact: true })).toBeVisible();

  await page.getByTestId("nmr-file-input").setInputFiles({
    name: "residues.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      `protein_id,sequence_number,residue_name,one_letter_code\n${protein.id},1,MET,M\n${protein.id},2,ALA,A\n`,
    ),
  });
  await page.getByRole("button", { name: "Preview validation" }).click();

  const preview = page.getByTestId("nmr-import-preview");
  await expect(preview).toContainText("All rows passed validation");
  await expect(preview.getByText("2", { exact: true })).toHaveCount(2);
  await page.getByRole("button", { name: "Import 2 rows" }).click();
  await page.getByRole("button", { name: "Import dataset" }).click();

  await expect(page.getByTestId("nmr-import-success")).toContainText("Imported 2 residues successfully");
  const residues = await request.get(`${apiBase}/nmr/residues?protein_id=${protein.id}`);
  expect((await residues.json()) as unknown[]).toHaveLength(2);
});

test("validation errors remain visible and cannot be imported", async ({ page }) => {
  await page.goto("/nmr-data");
  await page.getByRole("button", { name: "Import CSV" }).click();
  await page.getByTestId("nmr-file-input").setInputFiles({
    name: "bad-residues.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("protein_id,sequence_number,residue_name,one_letter_code\nmissing,not-a-number,MET,M\n"),
  });
  await page.getByRole("button", { name: "Preview validation" }).click();

  await expect(page.getByTestId("nmr-import-preview")).toContainText("Row 2");
  await expect(page.getByRole("button", { name: /Import \d+ rows/ })).toBeDisabled();
});
