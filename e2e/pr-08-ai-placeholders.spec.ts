import { expect, test } from '@playwright/test'

test('PR 8 demo loads AI placeholder contracts from the backend', async ({ page }) => {
  await page.goto('/ai-model')

  await expect(page.getByTestId('ai-page-title')).toHaveText('AI Model & MCP')
  await expect(page.getByTestId('ai-api-error')).toHaveCount(0)

  await expect(page.getByTestId('ai-settings-summary')).toContainText('PLACEHOLDER')
  await expect(page.getByTestId('analysis-module-count')).toHaveText('3')
  await expect(page.getByTestId('mcp-tool-count')).not.toHaveText('0')

  await expect(page.getByTestId('ai-provider-list')).toContainText('OpenAI API Key')
  await expect(page.getByTestId('local-runtime-list')).toContainText('Ollama')
  await expect(page.getByTestId('analysis-module-list')).toContainText('NMR Readiness Scoring')
  await expect(page.getByTestId('mcp-tool-list')).toContainText('/api/v1/ai/settings')
})
