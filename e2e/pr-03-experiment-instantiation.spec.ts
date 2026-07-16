import { expect, test } from '@playwright/test'

test('PR 3 experiment demo instantiates ANC2 and persists dialysis updates', async ({ page }) => {
  const note = `PR3 dialysis note ${Date.now()}`

  await page.goto('/workflow')
  await expect(page.getByText('ANC2 Purification Strategies')).toBeVisible()

  const previousExperimentId = await page.getByTestId('current-experiment-id').textContent().catch(() => null)
  await page.getByTestId('start-anc2-experiment').click()
  if (previousExperimentId) {
    await expect(page.getByTestId('current-experiment-id')).not.toHaveText(previousExperimentId)
  }
  await expect(page.getByTestId('current-experiment-title')).toContainText('ANC2 Experiment')
  await expect(page.getByTestId('experiment-batch-1-run')).toBeVisible()

  const batch1Run = page.getByTestId('experiment-batch-1-run')
  await batch1Run.getByLabel('Edit Dialysis').click({ force: true })

  const dialog = page.locator('[role="dialog"]').last()
  await dialog.locator('select').first().selectOption('complete')
  await dialog.locator('textarea').nth(1).fill(note)
  await dialog.getByTestId('save-step').click()

  const noteInRun = batch1Run.getByText(note, { exact: true })
  if (!(await noteInRun.isVisible().catch(() => false))) {
    const dialysisStep = batch1Run.locator('button').filter({ hasText: 'Dialysis' }).first()
    await dialysisStep.click()
  }
  await expect(noteInRun).toBeVisible()

  await page.reload()
  await expect(page.getByTestId('current-experiment-title')).toContainText('ANC2 Experiment')

  const reloadedBatch1Run = page.getByTestId('experiment-batch-1-run')
  const reloadedNoteInRun = reloadedBatch1Run.getByText(note, { exact: true })
  if (!(await reloadedNoteInRun.isVisible().catch(() => false))) {
    const reloadedDialysisStep = reloadedBatch1Run.locator('button').filter({ hasText: 'Dialysis' }).first()
    await reloadedDialysisStep.click()
  }
  await expect(reloadedNoteInRun).toBeVisible()
})
