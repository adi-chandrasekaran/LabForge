import { expect, test } from '@playwright/test'

test('PR 2 workflow library demo persists add, edit, and branch actions', async ({ page, request }) => {
  const stamp = Date.now()
  const stepName = `PR2 Demo Step ${stamp}`
  const editedStepName = `${stepName} Edited`
  const branchLabel = `PR2 Branch ${stamp}`

  await page.goto('/workflow')
  await expect(page.getByText('ANC2 Purification Strategies')).toBeVisible()
  await expect(page.getByText('Dialysis').first()).toBeVisible()

  await page.getByTestId('step-connector-b1-05').hover()
  await page.getByTestId('add-step-b1-05').click()
  await page.getByTestId('step-name-input').fill(stepName)
  await page.getByTestId('confirm-add-step').click()
  await expect(page.getByText(stepName)).toBeVisible()

  await page.getByLabel(`Edit ${stepName}`).click({ force: true })
  const labelInputs = page.locator('input').filter({ hasDisplayValue: stepName })
  await labelInputs.first().fill(editedStepName)
  await page.getByTestId('save-step').click()
  await expect(page.getByText(editedStepName)).toBeVisible()

  const workflows = await request.get('http://127.0.0.1:8017/api/v1/workflows')
  const workflowList = await workflows.json()
  const batch1Workflow = workflowList.find((workflow: { title: string }) => workflow.title === 'ANC2 Batch 1')
  const insertedStep = batch1Workflow?.steps.find((step: { label: string }) => step.label === editedStepName)
  expect(insertedStep?.id).toBeTruthy()

  const branchTrackActions = page.locator('[data-testid^="add-branch-step-"]')
  const branchTrackCountBefore = await branchTrackActions.count()
  await page.getByTestId(`step-connector-${insertedStep.id}`).hover()
  await page.getByTestId(`add-branch-${insertedStep.id}`).click()
  await page.getByTestId('branch-label-input').fill(branchLabel)
  await page.getByTestId('confirm-add-branch').click()
  await expect(branchTrackActions).toHaveCount(branchTrackCountBefore + 1)
  await expect(page.getByText(branchLabel, { exact: true })).toBeVisible()

  await page.reload()
  await expect(page.getByText(editedStepName).first()).toBeVisible()
  await expect(branchTrackActions).toHaveCount(branchTrackCountBefore + 1)
  await expect(page.getByText(branchLabel, { exact: true })).toBeVisible()
})
