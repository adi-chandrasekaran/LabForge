import { expect, test } from '@playwright/test'

test('four workflow functionality fixes demo', async ({ page, request }) => {
  const stamp = Date.now()
  const projectName = `Playwright Project ${stamp}`
  const projectCode = `PW-${stamp}`
  const standardName = `Playwright Standard ${stamp}`
  const standardizedSnapshotName = `RPC10 Snapshot ${stamp}`

  const projects = await request.get('http://127.0.0.1:8017/api/v1/projects')
  expect(projects.ok()).toBeTruthy()
  const projectTitles = (await projects.json()).map((project: { title: string }) => project.title)
  expect(projectTitles.sort()).toEqual([
    'ANC2 Protein Purification',
    'CCL20 Transformation And Culture',
    'RPC10 Purification Process And Troubleshooting',
  ].sort())

  await page.goto('/projects')
  await expect(page.getByText('ANC2 Protein Purification')).toBeVisible()
  await expect(page.getByText('RPC10 Purification Process And Troubleshooting')).toBeVisible()
  await expect(page.getByText('CCL20 Transformation And Culture')).toBeVisible()

  await page.getByText('NEW PROJECT').click()
  const projectDialog = page.locator('[role="dialog"]').last()
  await projectDialog.getByPlaceholder('e.g. ANC2 Crystallography').fill(projectName)
  await projectDialog.getByPlaceholder('e.g. XRAY-2026-08').fill(projectCode)
  await projectDialog.getByPlaceholder('Brief protocol description...').fill('Temporary project for workflow tab validation.')
  await projectDialog.getByPlaceholder('protein, NMR, structural').fill('temporary, playwright')
  await projectDialog.getByText('CREATE PROJECT').click()
  await expect(page.getByText(projectName)).toBeVisible()

  await page.goto('/workflow')
  await expect(page.getByRole('button', { name: 'ANC2' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'RPC10' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'CCL20' })).toBeVisible()
  await expect(page.getByRole('button', { name: projectName })).toBeVisible()

  await page.getByRole('button', { name: 'RPC10' }).click()
  await expect(page.getByText('RPC10 Purification / Troubleshooting')).toBeVisible()
  await expect(page.getByText('Split Into Two Batches')).toBeVisible()

  await page.getByRole('button', { name: 'CCL20' }).click()
  await expect(page.getByRole('heading', { name: 'CCL20 Transformation And Culture' }).first()).toBeVisible()
  await expect(page.getByText('Competent BL21 E. coli Cells')).toBeVisible()

  await page.goto('/standardized-workflows')
  await expect(page.getByRole('button', { name: /Ion Exchange Chromatography/ })).toBeVisible()
  await expect(page.getByRole('button', { name: /Reverse Nickel Chromatography/ })).toBeVisible()
  await page.getByTestId('new-standardized-workflow').click()
  await page.getByTestId('standardized-title-input').fill(standardName)
  await page.getByTestId('standardized-description-input').fill('Temporary standardized workflow for authoring validation.')
  await page.getByTestId('standardized-tags-input').fill('standardized, playwright')
  await page.getByTestId('standardized-save-metadata').click()
  await expect(page.getByRole('heading', { name: standardName })).toBeVisible()
  await page.getByTestId('standardized-add-step').click()
  const stepDialog = page.locator('[role="dialog"]').last()
  await stepDialog.locator('input').first().fill('Dummy standardized step')
  await stepDialog.locator('textarea').first().fill('Do the dummy standardized procedure.')
  await stepDialog.getByText('SAVE STEP').click()
  await expect(page.getByText('Dummy standardized step')).toBeVisible()

  await page.goto('/workflow')
  await page.getByRole('button', { name: 'RPC10' }).click()
  await page.getByTestId('workflow-add-step-workflow-rpc10-troubleshooting').click()
  await page.getByTestId('add-step-source').selectOption('standardized')
  await page.getByTestId('add-step-standardized-workflow').selectOption({ label: 'Ion Exchange Chromatography' })
  await page.getByText('Insert step').click()
  await expect(page.getByText('Prepare Low-Salt Start Buffer')).toBeVisible()

  await page.getByTestId('workflow-standardize-workflow-rpc10-troubleshooting').click()
  await page.getByTestId('standardize-modal').locator('input').first().fill(standardizedSnapshotName)
  await page.getByText('Save standard').click()
  await page.goto('/standardized-workflows')
  await expect(page.getByRole('button', { name: new RegExp(standardizedSnapshotName) })).toBeVisible()

  await page.getByRole('button', { name: new RegExp(standardName) }).click()
  await page.getByTestId('standardized-delete-workflow').click()
  await page.getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByText(standardName)).toHaveCount(0)

  await page.goto('/projects')
  await page.getByLabel(`Delete project ${projectName}`).click()
  await page.getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByText(projectName)).toHaveCount(0)
})
