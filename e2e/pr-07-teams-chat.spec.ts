import { expect, test } from '@playwright/test'

test('PR 7 demo creates a channel, posts a referenced message, and persists after reload', async ({ page }) => {
  const stamp = Date.now()
  const channelName = `anc2-pr7-${stamp}`
  const messageBody = `Dialysis precipitation check ${stamp}`

  await page.goto('/teams')
  await expect(page.getByRole('heading', { name: 'Teams & Chats' })).toBeVisible()
  await expect(page.getByText('general')).toBeVisible()

  await page.getByTestId('open-new-channel').click()
  const dialog = page.locator('[role="dialog"]').last()
  await dialog.getByTestId('new-channel-name').fill(channelName)
  await dialog.getByTestId('new-channel-topic').fill('Track ANC2 troubleshooting notes and gel images.')
  await dialog.getByTestId('confirm-create-channel').click()

  const createdChannel = page.locator('[data-testid^="channel-"]').filter({ hasText: channelName }).first()
  await expect(createdChannel).toBeVisible()

  await page.getByTestId('chat-message-body').fill(messageBody)
  await page.getByTestId('chat-workflow-reference').selectOption({ label: 'ANC2 Batch 1' })
  await page.getByTestId('chat-attachment-input').setInputFiles({
    name: 'dialysis-note.png',
    mimeType: 'image/png',
    buffer: Buffer.from('fake image bytes'),
  })
  await page.getByTestId('chat-send-message').click()

  await expect(page.getByText(messageBody)).toBeVisible()
  await expect(page.getByText('workflow · ANC2 Batch 1')).toBeVisible()
  await expect(page.getByAltText('dialysis-note.png')).toBeVisible()

  await page.reload()
  await expect(createdChannel).toBeVisible()
  await createdChannel.click()
  await expect(page.getByText(messageBody)).toBeVisible()
  await expect(page.getByAltText('dialysis-note.png')).toBeVisible()
})
