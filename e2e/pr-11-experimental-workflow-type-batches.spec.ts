import { expect, test } from "@playwright/test";

test("experimental workflow types and batches support independent live filtering and sorting", async ({ page }) => {
  await page.goto("/workflow");
  await expect(page.getByTestId("workflow-type-project-anc2")).toBeVisible();

  await page.getByTestId("workflow-type-search").fill("rpc");
  await expect(page.getByTestId("workflow-type-project-rpc10")).toBeVisible();
  await expect(page.getByTestId("workflow-type-project-anc2")).toHaveCount(0);

  await page.getByTestId("workflow-type-search").fill("");
  await page.getByLabel("Sort workflow types").selectOption("az");
  await page.getByTestId("workflow-type-project-anc2").click();
  await expect(page.getByTestId("workflow-batch-workflow-anc2-batch-1")).toBeVisible();

  await page.getByTestId("workflow-batch-search").fill("batch 2");
  await expect(page.getByTestId("workflow-batch-workflow-anc2-batch-2")).toBeVisible();
  await expect(page.getByTestId("workflow-batch-workflow-anc2-batch-1")).toHaveCount(0);
  await page.getByLabel("Sort batches").selectOption("oldest");
  await page.getByTestId("workflow-batch-workflow-anc2-batch-2").click();
  await expect(page.getByText("Refolding Protocol").first()).toBeVisible();
});
