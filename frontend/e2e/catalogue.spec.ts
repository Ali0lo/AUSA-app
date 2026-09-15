import { expect, test, type Route } from "@playwright/test";
import { catalogueRow } from "../src/test/catalogue";

async function respond(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

test("target catalogue follows degree and scores, labels missing data and recovers", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let fails = false;
  const requests: { level_sought: string; ielts?: number }[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/health")) return respond(route, { status: "healthy", service: "AUSA", version: "0.1.0", environment: "test" });
    if (url.pathname.endsWith("/catalogue/assess")) {
      if (fails) return respond(route, { detail: "Catalogue temporarily unavailable." }, 503);
      const profile = route.request().postDataJSON();
      requests.push(profile);
      const items = url.searchParams.get("university") === "Test University"
        ? [catalogueRow({ level: profile.level_sought, checks: [`IELTS supplied: ${profile.ielts ?? "unknown"}`] })] : [];
      return respond(route, { status: items.length ? "listed" : "not_collected", total: items.length, items });
    }
    if (url.pathname.endsWith("/catalogue")) return respond(route, { status: "listed", total: 1, items: [catalogueRow()] });
    return respond(route, { detail: "Unexpected test request" }, 501);
  });
  await page.goto("/plan");
  await page.getByRole("button", { name: "Target: Check a university" }).click();
  await page.getByLabel("I am applying for").selectOption("master");
  await page.getByLabel("What I hold now").selectOption("bachelor_degree");
  await page.getByLabel("Select or name a university to target").fill("Test University");
  await page.getByLabel("IELTS", { exact: true }).fill("6");
  await expect(page.getByText("IELTS supplied: 6", { exact: true })).toBeVisible();
  await page.getByLabel("IELTS", { exact: true }).fill("7.5");
  await expect(page.getByText("IELTS supplied: 7.5", { exact: true })).toBeVisible();
  expect(requests.at(-1)).toMatchObject({ level_sought: "master", ielts: 7.5 });
  await page.getByLabel("Select or name a university to target").fill("Uncollected University");
  await expect(page.getByText(/Requirements for this university and level have not been collected/)).toBeVisible();
  fails = true;
  await page.getByLabel("Select or name a university to target").fill("Test University");
  await expect(page.getByRole("button", { name: "Retry catalogue" })).toBeVisible();
  fails = false;
  await page.getByRole("button", { name: "Retry catalogue" }).click();
  await expect(page.getByText("IELTS supplied: 7.5", { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test("catalogue review requires acknowledgement and recovers from a stale revision", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const row = catalogueRow({ level: "bachelor" });
  const revision = "a".repeat(64);
  let conflict = true;
  let approved = false;
  await page.route("**/api/auth/session", (route) => respond(route, {
    user: { name: "Reviewer", email: "reviewer@example.edu", accessToken: "browser-test-token" },
    expires: "2099-01-01T00:00:00Z",
  }));
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) return respond(route, { status: "healthy", service: "AUSA", version: "0.1.0", environment: "test" });
    if (path.endsWith("/admin/catalogue/1/verify")) {
      expect(route.request().headers().authorization).toBe("Bearer browser-test-token");
      expect(route.request().postDataJSON()).toEqual({ revision, source_checked: true });
      if (conflict) return respond(route, { detail: "The row changed. Reload the review queue." }, 409);
      approved = true;
      return respond(route, { revision, requirement: { ...row, provenance: "human-verified" } });
    }
    if (path.endsWith("/admin/catalogue")) return respond(route, approved ? [] : [{ revision, requirement: row }]);
    return respond(route, []);
  });
  await page.goto("/admin");
  const review = page.getByRole("region", { name: "Admission catalogue review" });
  const verify = review.getByRole("button", { name: "Verify this catalogue row" });
  await expect(verify).toBeDisabled();
  await review.getByRole("checkbox").check();
  await verify.click();
  await expect(review.getByRole("alert")).toContainText("row changed");
  conflict = false;
  await review.getByRole("button", { name: "Reload review queue" }).click();
  await expect(verify).toBeDisabled();
  await review.getByRole("checkbox").check();
  await verify.click();
  await expect(review.getByText("No pending catalogue rows at this level.")).toBeVisible();
  expect(approved).toBe(true);
  expect(errors).toEqual([]);
});
