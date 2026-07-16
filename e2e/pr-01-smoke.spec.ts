import { expect, test } from '@playwright/test'

test('PR 1 smoke demo: app shell and backend health are reachable', async ({ page, request }) => {
  const health = await request.get('http://127.0.0.1:8017/api/v1/health')
  expect(health.ok()).toBeTruthy()
  await expect(await health.json()).toEqual({
    status: 'ok',
    app: 'NMR Lab Notebook API',
    database: 'reachable',
  })

  await page.goto('/')
  await expect(page.getByText(/LabNotebook|NMR Lab/i).first()).toBeVisible()
  await expect(page.getByText('HOME').first()).toBeVisible()
})
