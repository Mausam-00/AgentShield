import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => sessionStorage.setItem("as_intro_played_v1", "1"));
});

test("recorded replay animates to exact existing values and supports pause, resume and replay", async ({ page }, testInfo) => {
  const apiCalls: string[] = [];
  await page.route("**/api/**", route => { apiCalls.push(route.request().url()); return route.abort(); });
  await page.goto("/");
  const replay = page.locator(".benchmark-replay");
  await replay.scrollIntoViewIfNeeded();
  await expect(replay).toHaveAttribute("data-running", "true");
  await expect(replay).toContainText("not a live engine run");
  await page.getByRole("button", { name: "Pause replay", exact: true }).click();
  await expect(replay).toHaveAttribute("data-running", "false");
  const paused = await replay.getByTestId("replay-value").allTextContents();
  await page.waitForTimeout(300);
  expect(await replay.getByTestId("replay-value").allTextContents()).toEqual(paused);
  await page.getByRole("button", { name: "Resume replay", exact: true }).click();
  await expect(replay).toHaveAttribute("data-complete", "true", { timeout: 15000 });
  await expect(replay.getByTestId("replay-value")).toHaveText(["162,833", "91"]);
  expect(await replay.getByTestId("baseline-bar").evaluateAll(elements => elements.map(el => (el as HTMLElement).style.width))).toEqual(["100%", "100%"]);
  expect(await replay.getByTestId("optimized-bar").evaluateAll(elements => elements.map(el => (el as HTMLElement).style.width))).toEqual(["67%", "46%"]);
  await expect(replay.locator(".benchmark-preserved")).toHaveAttribute("data-highlighted", "true");
  await expect(replay).toContainText("12 / 12");
  await expect(replay).toContainText("0 · byte-identical");
  await expect(replay).toContainText("not provider-exact");
  await replay.screenshot({ path: testInfo.outputPath("benchmark-complete.png") });
  await page.getByRole("button", { name: "Replay benchmark", exact: true }).click();
  await expect(replay).toHaveAttribute("data-complete", "false");
  await expect(replay.getByTestId("replay-value")).toHaveText(["244,476", "196"]);
  await page.getByRole("button", { name: "Pause replay", exact: true }).click();
  await page.locator("h1").scrollIntoViewIfNeeded();
  await replay.scrollIntoViewIfNeeded();
  await expect(replay).toHaveAttribute("data-running", "false");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(replay).toHaveAttribute("data-complete", "true");
  await expect(replay.getByTestId("replay-value")).toHaveText(["162,833", "91"]);
  expect(apiCalls).toEqual([]);
});

test("benchmark pauses offscreen and when the tab is hidden", async ({ page }) => {
  await page.goto("/");
  const replay = page.locator(".benchmark-replay");
  await replay.scrollIntoViewIfNeeded();
  await expect(replay).toHaveAttribute("data-running", "true");
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(replay).toHaveAttribute("data-running", "false");
  await page.evaluate(() => {
    Reflect.deleteProperty(document, "hidden");
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(replay).toHaveAttribute("data-running", "true");
  await page.locator("h1").scrollIntoViewIfNeeded();
  await expect(replay).toHaveAttribute("data-running", "false");
  const values = await replay.getByTestId("replay-value").allTextContents();
  await page.waitForTimeout(300);
  expect(await replay.getByTestId("replay-value").allTextContents()).toEqual(values);
});

test("reduced motion shows final benchmark values and keeps original details expandable", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const replay = page.locator(".benchmark-replay");
  await replay.scrollIntoViewIfNeeded();
  await expect(replay).toHaveAttribute("data-complete", "true");
  await expect(replay).toHaveAttribute("data-running", "false");
  await expect(replay.getByTestId("replay-value")).toHaveText(["162,833", "91"]);
  await expect(replay.getByRole("button", { name: "Recorded results", exact: true })).toBeDisabled();
  await replay.locator(".benchmark-metric").first().getByRole("button", { name: "Click for more info" }).click();
  await expect(replay).toContainText("approximated as characters ÷ 4");
});
