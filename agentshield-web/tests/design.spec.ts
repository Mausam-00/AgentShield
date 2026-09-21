import { expect, test, type Page } from "@playwright/test";

async function skipBoot(page: Page) {
  await page.addInitScript(() => sessionStorage.setItem("as_intro_played_v1", "1"));
  await page.goto("/");
}

async function openAbout(page: Page) {
  const menu = page.getByRole("button", { name: "Open menu", exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("button", { name: "About Us", exact: true }).click();
}

async function uploadFixture(page: Page) {
  await page.locator('input[type="file"]').setInputFiles({
    name: "synthetic-agent.agent.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("---\nname: Synthetic test agent\n---\nRead-only test fixture."),
  });
  await page.getByRole("button", { name: "Run assessment", exact: true }).click();
}

async function revealNeuralScene(page: Page) {
  await page.locator('.neural-viewport[data-variant="shield"]').scrollIntoViewIfNeeded();
  await expect(page.locator(".neural-scene")).toBeVisible();
  await expect(page.locator('.neural-viewport[data-variant="shield"]')).toHaveAttribute("data-active", "true");
}

test("opening sequence plays, is skippable and retains its session behavior", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("boot-intro")).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("boot-intro")).toHaveCount(0);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("autonomous");
  await page.reload();
  await revealNeuralScene(page);
  await expect(page.getByTestId("boot-intro")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.style.overflow)).toBe("");
});

test("neural hero, gate pathway and original content work without horizontal overflow", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await skipBoot(page);
  await revealNeuralScene(page);
  await expect(page.getByText("AI advises — never authorizes.", { exact: false })).toBeVisible();
  const nodes = page.locator(".gate-button");
  await expect(nodes).toHaveCount(8);
  for (let i = 0; i < 8; i++) {
    await nodes.nth(i).focus();
    await expect(nodes.nth(i)).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("#gate-detail")).toHaveAttribute("aria-labelledby", `gate-G${i}`);
    await expect(page.locator("#gate-detail")).toContainText(`G${i}`);
  }
  await expect(page.locator('.neural-viewport[data-variant="shield"]')).toHaveAttribute("data-active", "false");
  await expect(page.locator(".feature-panel")).toHaveCount(6);
  await expect(page.locator(".trust-lane")).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("gates.png") });
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({ path: testInfo.outputPath("hero.png") });
});

test("About keeps the zipper, contains keyboard focus and restores scroll after Escape", async ({ page }) => {
  await skipBoot(page);
  await openAbout(page);
  const dialog = page.getByRole("dialog", { name: "About AgentShield AI" });
  await expect(dialog).toBeVisible();
  await expect(dialog.locator(".zip-panel")).toHaveCount(2);
  await expect(dialog.locator(".zip-pull")).toHaveCount(1);
  await expect(dialog.getByRole("heading", { name: "Non-negotiable principles" })).toBeAttached();
  await expect(page.getByTestId("zip-curtain")).toHaveCSS("transform", /matrix/);
  await expect.poll(() => page.getByTestId("zip-curtain").evaluate(el => el.getBoundingClientRect().right)).toBeLessThan(0);
  await page.keyboard.press("Tab");
  expect(await dialog.evaluate(el => el.contains(document.activeElement))).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  expect(await page.evaluate(() => document.body.style.overflow)).toBe("");
});

test("assessment retains radar, stages and result values until the response arrives", async ({ page }, testInfo) => {
  let finishResponse!: () => void;
  const waiting = new Promise<void>(resolve => { finishResponse = resolve; });
  await page.route("**/api/assess", async route => {
    await waiting;
    await route.fulfill({ json: {
      // Synthetic browser fixture, not an engine measurement.
      summary: { subject: "Synthetic test agent", assurance_score: 68, findings_count: 4,
        assurance_posture: "WARN", runtime_decision: "ALLOW", redteam_posture: "WARN",
        defense_coverage: .2, residual_exposure: .8, rai_posture: "BLOCK" },
      html: "<p>Synthetic browser-test fixture</p>",
    } });
  });
  await skipBoot(page);
  await uploadFixture(page);
  const loader = page.getByRole("status", { name: "Assessment in progress" });
  await expect(loader).toBeVisible();
  await expect(loader.locator(".processing-node")).toHaveCount(8);
  await expect(loader).toContainText("not live progress");
  await expect(page.getByRole("button", { name: "Assessing…" })).toBeDisabled();
  await loader.screenshot({ path: testInfo.outputPath("assessment-loader.png") });
  finishResponse();
  await expect(loader).toHaveCount(0);
  await expect(page.getByText("4 open findings", { exact: true })).toBeVisible();
  await expect(page.locator("#demo").getByText("ALLOW", { exact: true })).toBeVisible();
  await expect(page.locator("#demo").getByText("68", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Download report" })).toBeEnabled();
  await page.locator(".assessment-workspace").screenshot({ path: testInfo.outputPath("assessment-result.png") });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("failed assessment releases the loader and allows retry", async ({ page }) => {
  await page.route("**/api/assess", route => route.fulfill({
    status: 500, json: { error: "Synthetic engine failure" },
  }));
  await skipBoot(page);
  await uploadFixture(page);
  await expect(page.getByText("Synthetic engine failure", { exact: true })).toBeVisible();
  await expect(page.getByRole("status", { name: "Assessment in progress" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Run assessment", exact: true })).toBeEnabled();
});

test("reduced motion keeps the three experiences usable without continuous animation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByTestId("boot-intro")).toHaveCount(0, { timeout: 5000 });
  await revealNeuralScene(page);
  await expect(page.locator(".neural-orbit")).toHaveCSS("animation-name", "none");
  await openAbout(page);
  await expect.poll(() => page.getByTestId("zip-curtain").evaluate(el => el.getBoundingClientRect().right)).toBeLessThan(0);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "About AgentShield AI" })).toHaveCount(0);
  let release!: () => void;
  const waiting = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/assess", async route => {
    await waiting;
    await route.fulfill({ status: 500, json: { error: "Synthetic stopped request" } });
  });
  await uploadFixture(page);
  const loader = page.getByRole("status", { name: "Assessment in progress" });
  await expect(loader).toBeVisible();
  await expect(loader).toContainText("Intercepting the proposed action");
  await page.waitForTimeout(1100);
  await expect(loader).toContainText("Intercepting the proposed action");
  release();
  await expect(loader).toHaveCount(0);
});
