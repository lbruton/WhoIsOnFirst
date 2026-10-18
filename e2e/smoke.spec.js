import { test, expect } from '@playwright/test';

test.describe('WhoIsOnFirst Smoke Tests', () => {
  test('app loads', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });
});
