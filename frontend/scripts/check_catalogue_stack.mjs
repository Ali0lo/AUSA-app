// Launched by python -m scripts.check_catalogue_stack, against disposable data.
import assert from "node:assert/strict";
import { chromium, expect } from "@playwright/test";

const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH || undefined });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const response = await page.request.get("http://127.0.0.1:8000/api/v1/catalogue?level=master");
  assert.equal(response.status(), 200);
  assert.equal((await response.json()).total, 30);
  await page.goto("http://127.0.0.1:3100/plan");
  await page.getByRole("button", { name: "Target: Check a university" }).click();
  await page.getByLabel("I am applying for").selectOption("master");
  await page.getByLabel("What I hold now").selectOption("bachelor_degree");
  await page.getByLabel("Select or name a university to target").fill("UCL");
  await page.getByLabel("IELTS", { exact: true }).fill("6");
  const target = page.getByRole("region", { name: "Target university requirements" });
  await expect(target.getByText("Computer Science", { exact: true })).toBeVisible();
  await expect(target.getByText(/Your IELTS 6 is below the recorded 7/)).toHaveCount(3);
  await expect(target.getByText(/still awaits human review/)).toHaveCount(3);
  await page.getByLabel("IELTS", { exact: true }).fill("7.5");
  await expect(target.getByText(/Your IELTS meets the recorded overall minimum/)).toHaveCount(3);
  await page.getByLabel("Select or name a university to target").fill("Uncollected University");
  await expect(target.getByText(/Requirements for this university and level have not been collected/)).toBeVisible();
  assert.deepEqual(errors, []);
  console.log("PASS: production Next.js + live FastAPI + disposable SQL catalogue; 30 masters, UCL requirements, score changes, review caveats, missing university, no browser exceptions.");
} finally {
  await browser.close();
}
