import { expect, test } from "@playwright/test";

test("standardized workflows are grouped under workflow types", async ({ page }) => {
  await page.goto("/standardized-workflows");
  await page.getByTestId("workflow-type-project-shared-methods").click();
  await expect(page.getByTestId("workflow-batch-workflow-standard-reverse-nickel")).toBeVisible();
  await page.getByTestId("workflow-batch-search").fill("ion");
  await expect(page.getByTestId("workflow-batch-workflow-standard-ion-exchange")).toBeVisible();
  await page.getByLabel("Sort batches").selectOption("za");
});
