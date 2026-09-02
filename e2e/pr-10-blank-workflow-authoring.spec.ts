import { expect, test } from '@playwright/test'

test('blank experimental workflow can be authored with detailed steps and branches', async ({ page }) => {
  const stamp = Date.now()
  const projectName = `Blank Workflow Project ${stamp}`
  const projectCode = `BLANK-${stamp}`
  const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? '8017'
  const backendUrl = `http://127.0.0.1:${backendPort}`

  const createProject = await page.request.post(`${backendUrl}/api/v1/projects`, {
    data: {
      title: projectName,
      code: projectCode,
      description: 'Temporary project for blank workflow authoring.',
      status: 'active',
      tags: ['temporary', 'blank-workflow'],
    },
  })
  expect(createProject.ok()).toBeTruthy()

  await page.goto('/workflow')
  await page.getByRole('button', { name: projectName }).click()
  await page.getByRole('button', { name: 'CREATE BLANK WORKFLOW' }).click()

  await expect(page.getByTestId('add-step-modal')).toBeVisible()
  await page.getByTestId('step-label-input').fill('Prepare starter culture')
  await page.getByTestId('step-sublabel-input').fill('overnight growth')
  await page.getByTestId('step-status-input').selectOption('running')
  await page.getByTestId('step-duration-input').fill('16 hr')
  await page.getByTestId('step-procedure-input').fill('Inoculate LB antibiotic media and grow overnight at 37 C.')
  await page.getByTestId('step-inputs-input').fill('sample | picked colony | 1 colony | from fresh plate\nbuffer | LB + antibiotic | 5 mL | sterile tube')
  await page.getByTestId('step-parameters-input').fill('Temperature | 37 C\nShaking | 220 rpm')
  await page.getByTestId('step-outputs-input').fill('sample | starter culture | 5 mL | ready for expression test')
  await page.getByTestId('step-notes-input').fill('Expected cloudy growth by morning.')
  await page.getByText('Insert step').click()

  const starterStep = page.locator('[data-testid^="workflow-step-"]').filter({ hasText: 'Prepare starter culture' }).first()
  await expect(starterStep).toBeVisible()
  await starterStep.click()
  await expect(page.getByText('Temperature:')).toBeVisible()
  await expect(page.locator('b').filter({ hasText: '37 C' })).toBeVisible()

  await starterStep.hover()
  await page.locator('button[title="Diverge branch"]').first().click()
  await page.getByTestId('branch-source').selectOption('manual')
  await page.getByPlaceholder('Troubleshooting branch').fill('Low growth troubleshooting')
  await page.getByText('Create branch').click()
  await expect(page.getByText('Branch: Low growth troubleshooting')).toBeVisible()

  await page.getByText('+ Add branch step').click()
  await expect(page.getByTestId('add-branch-step-modal')).toBeVisible()
  await page.getByTestId('step-label-input').fill('Check antibiotic plate')
  await page.getByTestId('step-duration-input').fill('10 min')
  await page.getByTestId('step-procedure-input').fill('Confirm the colony came from the correct antibiotic plate.')
  await page.getByTestId('step-parameters-input').fill('Plate antibiotic | kanamycin')
  await page.getByTestId('step-outputs-input').fill('data | plate check | pass/fail | troubleshoot selection')
  await page
    .getByTestId('add-branch-step-modal')
    .getByRole('button', { name: 'Add branch step' })
    .click()
  await expect(page.getByText('Check antibiotic plate')).toBeVisible()

  await page.reload()
  await page.getByRole('button', { name: projectName }).click()
  const persistedStarterStep = page.locator('[data-testid^="workflow-step-"]').filter({ hasText: 'Prepare starter culture' }).first()
  await expect(persistedStarterStep).toBeVisible()
  await persistedStarterStep.click()
  await expect(page.getByText('Low growth troubleshooting')).toBeVisible()
  await expect(page.getByText('Check antibiotic plate')).toBeVisible()

  await page.goto('/projects')
  await page.getByLabel(`Delete project ${projectName}`).click()
  await page.getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByText(projectName)).toHaveCount(0)
})
