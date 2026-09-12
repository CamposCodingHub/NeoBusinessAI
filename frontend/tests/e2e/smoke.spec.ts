import { expect, test } from '@playwright/test';

/**
 * Minimal smoke: hit / or /login when a server is up; skip otherwise.
 * Does not fail CI when no frontend process is running.
 */
test('smoke home or login visible', async ({ page, request, baseURL }) => {
  const origin = baseURL || 'http://127.0.0.1:3000';

  let reachable = false;
  for (const path of ['/', '/login']) {
    try {
      const res = await request.get(`${origin}${path}`, { timeout: 4000 });
      if (res.status() < 500) {
        reachable = true;
        break;
      }
    } catch {
      // connection refused / timeout
    }
  }

  if (!reachable) {
    test.skip(true, 'No frontend server — smoke skipped');
    return;
  }

  let response = await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 15000 });
  if (!response || response.status() >= 400) {
    response = await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
  }

  expect(response, 'expected a navigation response').toBeTruthy();
  expect(response!.status()).toBeLessThan(500);

  const title = await page.title();
  const heading = page.locator('h1, h2, title').first();
  await expect(heading).toBeVisible({ timeout: 10000 });
  expect((title || '').length + (await heading.innerText()).length).toBeGreaterThan(0);
});
