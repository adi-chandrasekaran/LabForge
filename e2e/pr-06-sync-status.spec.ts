import { expect, test } from '@playwright/test'

test('PR 6 demo shows local save state and placeholder sync status', async ({ page }) => {
  const timestamp = Date.now()
  const projectName = `PR6 Sync Project ${timestamp}`
  const projectCode = `SYNC-${timestamp}`

  await page.goto('/')
  await expect(page.getByText(/LOCAL IDLE|SAVED LOCALLY/)).toBeVisible()

  await page.goto('/projects')
  await page.getByText('NEW PROJECT').click()
  const dialog = page.locator('[role="dialog"]').last()
  await dialog.getByPlaceholder('e.g. ANC2 Crystallography').fill(projectName)
  await dialog.getByPlaceholder('e.g. XRAY-2026-08').fill(projectCode)
  await dialog.getByPlaceholder('Brief protocol description...').fill('PR6 sync status project creation demo.')
  await dialog.getByPlaceholder('protein, NMR, structural').fill('sync, demo')
  await dialog.getByText('CREATE PROJECT').click()

  await expect(page.getByText(projectName)).toBeVisible()
  await expect(page.locator('aside').getByText('SAVED LOCALLY', { exact: true })).toBeVisible()
  await expect(page.getByText(/pending/i)).toBeVisible()

  await page.getByRole('button', { name: 'SYNC' }).click()
  await expect(page.getByText(/Hosted sync is not configured in local mode|Hosted sync is not implemented yet/)).toBeVisible()
})
