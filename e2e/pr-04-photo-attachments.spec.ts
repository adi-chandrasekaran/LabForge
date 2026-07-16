import { expect, test } from '@playwright/test'

const PNG_BUFFER = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNgYGD4DwABBAEAX8ICnQAAAABJRU5ErkJggg==',
  'base64',
)

test('PR 4 attachment demo uploads and deletes images on workflow and experiment steps', async ({ page }) => {
  const workflowAttachmentName = `workflow-gel-${Date.now()}.png`
  const experimentAttachmentName = `experiment-gel-${Date.now()}.png`

  await page.goto('/workflow')
  await expect(page.getByText('ANC2 Purification Strategies')).toBeVisible()

  await page.getByTestId('edit-step-b1-08').click({ force: true })
  let dialog = page.locator('[role="dialog"]').last()
  await dialog.getByTestId('attachment-file-input').setInputFiles({
    name: workflowAttachmentName,
    mimeType: 'image/png',
    buffer: PNG_BUFFER,
  })
  await expect(dialog.getByText(workflowAttachmentName)).toBeVisible()
  await dialog.getByTestId('save-step').click()

  await page.reload()
  await page.getByTestId('edit-step-b1-08').click({ force: true })
  dialog = page.locator('[role="dialog"]').last()
  await expect(dialog.getByText(workflowAttachmentName)).toBeVisible()
  await dialog.getByLabel(`Delete attachment ${workflowAttachmentName}`).click()
  await expect(dialog.getByText(workflowAttachmentName)).toHaveCount(0)
  await dialog.getByTestId('save-step').click()

  const previousExperimentId = await page.getByTestId('current-experiment-id').textContent().catch(() => null)
  await page.getByTestId('start-anc2-experiment').click()
  await expect(page.getByTestId('current-experiment-id')).not.toHaveText(previousExperimentId ?? '')
  const batch1Run = page.getByTestId('experiment-batch-1-run')
  await expect(page.getByTestId('current-experiment-title')).toContainText('ANC2 Experiment')
  await batch1Run.getByLabel('Edit Dialysis').click({ force: true })

  dialog = page.locator('[role="dialog"]').last()
  await dialog.getByTestId('attachment-file-input').setInputFiles({
    name: experimentAttachmentName,
    mimeType: 'image/png',
    buffer: PNG_BUFFER,
  })
  await expect(dialog.getByText(experimentAttachmentName)).toBeVisible()
  await dialog.getByTestId('save-step').click()

  await page.reload()
  await page.getByTestId('experiment-batch-1-run').getByLabel('Edit Dialysis').click({ force: true })
  dialog = page.locator('[role="dialog"]').last()
  await expect(dialog.getByText(experimentAttachmentName)).toBeVisible()
  await dialog.getByLabel(`Delete attachment ${experimentAttachmentName}`).click()
  await expect(dialog.getByText(experimentAttachmentName)).toHaveCount(0)
})
