import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => sessionStorage.setItem("as_intro_played_v1", "1"));
});

test("three scenes render in the appropriate mode and follow existing selections", async ({ page, isMobile }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/");
  for (const variant of ["shield", "capabilities", "gates"]) {
    const scene = page.locator(`.neural-viewport[data-variant="${variant}"]`);
    await scene.scrollIntoViewIfNeeded();
    await expect(scene).toHaveAttribute("data-active", "true");
    await expect(scene).toHaveAttribute("data-renderer", isMobile ? "svg" : "webgl", { timeout: 15000 });
    await expect(scene.locator(".shield-webgl canvas")).toHaveCount(isMobile ? 0 : 1);
    await scene.screenshot({ path: testInfo.outputPath(`${variant}.png`) });
  }
  await page.locator(".feature-panel").nth(1).click();
  await expect(page.locator('[data-variant="capabilities"]')).toHaveAttribute("data-selected", "1");
  await expect(page.locator(".feature-panel").nth(1)).toHaveAttribute("aria-expanded", "true");
  await page.locator("#gate-G6").focus();
  await expect(page.locator('[data-variant="gates"]')).toHaveAttribute("data-selected", "6");
  await expect(page.locator("#gate-detail")).toHaveAttribute("aria-labelledby", "gate-G6");
  await expect(page.locator('[data-variant="shield"]')).toHaveAttribute("data-active", "false");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test("WebGL really animates and context loss restores the section fallback", async ({ page, isMobile }) => {
  test.skip(isMobile, "Mobile deliberately uses SVG instead of WebGL.");
  await page.goto("/");
  const scene = page.locator('[data-variant="capabilities"]');
  await scene.scrollIntoViewIfNeeded();
  await expect(scene).toHaveAttribute("data-renderer", "webgl", { timeout: 15000 });
  // Isolate the 3D output from the independently moving background.
  await page.addStyleTag({ content: ".ambient-network { visibility: hidden; }" });
  const before = await scene.screenshot();
  await page.waitForTimeout(400);
  expect((await scene.screenshot()).equals(before)).toBe(false);
  await scene.locator("canvas").evaluate(canvas => canvas.dispatchEvent(new Event("webglcontextlost", { cancelable: true })));
  await expect(scene).toHaveAttribute("data-renderer", "svg");
  await expect(scene.locator(".section-scene-fallback")).toBeVisible();
  await expect(scene.locator("canvas")).toHaveCount(0);
});

test("unsupported WebGL retains all SVG illustrations", async ({ page, isMobile }) => {
  test.skip(isMobile, "WebGL is never attempted on mobile.");
  const warnings: string[] = [];
  page.on("console", message => {
    if (message.type() === "warning" && message.text().startsWith("AgentShield:")) warnings.push(message.text());
  });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      value: function (this: HTMLCanvasElement, ...args: Parameters<typeof original>) {
        if (String(args[0]).includes("webgl")) return null;
        return Reflect.apply(original, this, args);
      },
    });
  });
  await page.goto("/");
  for (const variant of ["shield", "capabilities", "gates"]) {
    const scene = page.locator(`[data-variant="${variant}"]`);
    await scene.scrollIntoViewIfNeeded();
    await expect(scene.locator(variant === "shield" ? ".neural-scene" : ".section-scene-fallback")).toBeVisible();
    await expect(scene).toHaveAttribute("data-renderer", "svg");
    await expect.poll(() => warnings.length).toBeGreaterThan(["shield", "capabilities", "gates"].indexOf(variant));
    await expect(scene.locator(".shield-webgl")).toHaveCount(0);
  }
});

test("background moves, pauses when hidden, and becomes static with reduced motion", async ({ page, isMobile }) => {
  await page.goto("/");
  const canvas = page.locator(".ambient-network canvas");
  const pixels = () => canvas.evaluate(el => (el as HTMLCanvasElement).toDataURL());
  await expect(canvas).toHaveAttribute("data-motion", "animated");
  const first = await pixels();
  await expect.poll(pixels).not.toBe(first);
  const hero = page.locator('[data-variant="shield"]');
  await hero.scrollIntoViewIfNeeded();
  if (!isMobile) await expect(hero).toHaveAttribute("data-renderer", "webgl", { timeout: 15000 });
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(canvas).toHaveAttribute("data-motion", "paused");
  await expect(hero).toHaveAttribute("data-active", "false");
  const paused = await pixels();
  await page.waitForTimeout(200);
  expect(await pixels()).toBe(paused);
  await page.evaluate(() => {
    Reflect.deleteProperty(document, "hidden");
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(canvas).toHaveAttribute("data-motion", "animated");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(canvas).toHaveAttribute("data-motion", "static");
  await expect(hero).toHaveAttribute("data-renderer", "svg");
  await expect(hero.locator("canvas")).toHaveCount(0);
  const still = await pixels();
  await page.waitForTimeout(200);
  expect(await pixels()).toBe(still);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await expect(canvas).toHaveAttribute("data-motion", "animated");
  if (!isMobile) await expect(hero).toHaveAttribute("data-renderer", "webgl", { timeout: 15000 });
});

test("CTA security illustration preserves the copy and link and respects motion settings", async ({ page }, testInfo) => {
  await page.goto("/");
  const cta = page.locator(".security-cta");
  await cta.scrollIntoViewIfNeeded();
  const illustration = cta.locator(".security-perimeter");
  await expect(illustration).toHaveAttribute("aria-hidden", "true");
  await expect(illustration).toHaveAttribute("data-active", "true");
  await expect(cta.getByRole("heading")).toHaveText("Put a control plane in front of every agent.");
  await expect(cta).toContainText("a 30-minute technical walkthrough.");
  await expect(cta.getByRole("link", { name: "Get it on GitHub" })).toHaveAttribute("href", "https://github.com/Mausam-00/AgentShield");
  await cta.screenshot({ path: testInfo.outputPath("security-cta.png") });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(illustration.locator(".perimeter-ring")).toHaveCSS("animation-name", "none");
  await page.locator("h1").scrollIntoViewIfNeeded();
  await expect(illustration).toHaveAttribute("data-active", "false");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
