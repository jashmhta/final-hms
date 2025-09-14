import { test, expect } from "@playwright/test";

test("has title", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/HMS/);
});

test("login flow", async ({ page }) => {
  await page.goto("/login");

  await page.fill('input[name="username"]', "testuser");
  await page.fill('input[name="password"]', "testpass");
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL(/\/dashboard/);
});
