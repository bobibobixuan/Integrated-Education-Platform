import { test, expect } from '@playwright/test'

test('login page loads', async ({ page }) => {
  await page.goto('/app/')
  await expect(page.locator('form')).toBeVisible()
  await expect(page.locator('input[type="text"]')).toBeVisible()
  await expect(page.locator('input[type="password"]')).toBeVisible()
})
