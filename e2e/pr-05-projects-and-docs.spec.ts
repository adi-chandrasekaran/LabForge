import { expect, test } from '@playwright/test'

test('PR 5 demo loads persisted home/profile/projects/docs data', async ({ page }) => {
  const timestamp = Date.now()
  const projectName = `SEC Optimization ${timestamp}`
  const projectCode = `SEC-${timestamp}`

  await page.goto('/')
  await expect(page.getByText(/Good (morning|afternoon|evening),/)).toBeVisible()
  await expect(page.getByText('RECENT PROJECTS')).toBeVisible()
  await expect(page.getByText('RECENT ACTIVITY')).toBeVisible()

  await page.goto('/profile')
  await expect(page.getByRole('main').getByText('Chen, Y.')).toBeVisible()
  await expect(page.getByRole('main').getByText('Protein Purification')).toBeVisible()

  await page.goto('/projects')
  await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible()
  await expect(page.getByText('ANC2 Protein Purification')).toBeVisible()

  await page.getByText('NEW PROJECT').click()
  const dialog = page.locator('[role="dialog"]').last()
  await dialog.getByPlaceholder('e.g. ANC2 Crystallography').fill(projectName)
  await dialog.getByPlaceholder('e.g. XRAY-2026-08').fill(projectCode)
  await dialog.getByPlaceholder('Brief protocol description...').fill('Track SEC conditions and pooled fractions.')
  await dialog.getByPlaceholder('protein, NMR, structural').fill('sec, anc2')
  await dialog.getByText('CREATE PROJECT').click()

  await expect(page.getByText(projectName)).toBeVisible()
  await page.reload()
  await expect(page.getByText(projectName)).toBeVisible()

  await page.goto('/docs')
  await expect(page.getByRole('heading', { name: 'Documentation' })).toBeVisible()
  await page.getByText('Workflow Library').click()
  await expect(page.getByText('ANC2 Batch 1 and Batch 2 are the reference workflows')).toBeVisible()
})
