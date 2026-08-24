import { expect, Page, Route, test } from "@playwright/test";

const health = {
  status: "healthy",
  service: "AUSA",
  version: "0.1.0",
  environment: "test"
};

const factor = (score: number, passed: boolean, explanation: string) => ({
  score,
  weight: 0.25,
  weighted_score: score * 0.25,
  passed_hard_filter: passed,
  explanation
});

const matchResult = {
  program_name: "BSc Data Science",
  university_name: "University College London (UCL)",
  overall_match_percentage: 72,
  is_eligible: true,
  ineligibility_reasons: [],
  breakdown: {
    degree_level: factor(100, true, "The degree level matches."),
    academic: factor(88, true, "The GPA meets the minimum."),
    budget: factor(40, false, "The budget is below the listed tuition."),
    language: factor(60, true, "The language result meets the minimum.")
  }
};

function monitorErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource:")) {
      errors.push(message.text());
    }
  });
  return errors;
}

test.beforeEach(async ({ request }) => {
  const response = await request.get("/api/auth/session");
  expect(response.ok()).toBe(true);
});

async function respond(route: Route, data: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(data)
  });
}

async function mockHealth(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) {
      await respond(route, health);
      return;
    }
    await respond(route, { detail: "This test did not configure the requested endpoint." }, 501);
  });
}

test("landing search, navigation, and mobile menu always produce an outcome", async ({ page }) => {
  const errors = monitorErrors(page);
  await mockHealth(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "A clearer route to the right programme." })).toBeVisible();
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();
  const search = page.getByRole("combobox", { name: "Search the demo programme catalogue" });
  await page.getByRole("button", { name: "Search demo" }).click();
  await expect(page.getByText(/Enter a programme, university, field, or country/)).toBeVisible();

  await search.fill("not in this catalogue");
  await page.getByRole("button", { name: "Search demo" }).click();
  await expect(page.getByText(/full catalogue is not implemented/)).toBeVisible();

  await search.fill("UCL");
  await page.getByRole("button", { name: "Search demo" }).click();
  await expect(page).toHaveURL(/\/match\?program=102$/);
  await expect(page.locator("button[aria-pressed='true']")).toContainText("University College London");
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.locator("#mobile-navigation").getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Mobile navigation" })).toBeVisible();
  await page.getByRole("button", { name: "Close navigation" }).click();
  await expect(page.getByRole("navigation", { name: "Mobile navigation" })).toHaveCount(0);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("link", { name: "AI advisor" }).click();
  await expect(page).toHaveURL(/\/advisor$/);
  await expect(page.getByRole("navigation", { name: "Mobile navigation" })).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("matching submits the preserved contract, reports failure, retries, and resets", async ({ page }) => {
  const errors = monitorErrors(page);
  let matchingFails = false;
  let submitted: Record<string, unknown> | null = null;
  let healthChecks = 0;

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) {
      healthChecks += 1;
      await respond(route, health);
      return;
    }
    if (path.endsWith("/matching/evaluate")) {
      submitted = route.request().postDataJSON();
      await respond(route, matchingFails ? { detail: "Scoring service maintenance." } : matchResult, matchingFails ? 503 : 200);
      return;
    }
    await respond(route, { detail: "Unknown test endpoint." }, 404);
  });

  await page.goto("/match");
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(page.getByText("Backend online · v0.1.0")).toBeVisible();
  await page.getByRole("button", { name: "Check again" }).click();
  await expect.poll(() => healthChecks).toBeGreaterThanOrEqual(2);

  const ucl = page.locator("button").filter({ hasText: "University College London (UCL)" });
  await ucl.click();
  await page.getByLabel("Target degree").selectOption("bachelor");
  await page.getByRole("button", { name: "Evaluate compatibility" }).click();

  await expect(page.getByRole("heading", { name: "BSc Data Science" })).toBeVisible();
  await expect(page.getByText("72%")).toBeVisible();
  expect(submitted).toMatchObject({
    student: { degree_level: "bachelor" },
    program: { program_id: 102, university_name: "University College London (UCL)" }
  });

  await page.getByRole("button", { name: "Evaluate another profile" }).click();
  await expect(page.getByRole("heading", { name: "Your backend response will appear here." })).toBeVisible();
  matchingFails = true;
  await page.getByRole("button", { name: "Evaluate compatibility" }).click();
  await expect(page.getByText("Scoring service maintenance.", { exact: true })).toBeVisible();

  matchingFails = false;
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByText("72%")).toBeVisible();
  await page.getByRole("button", { name: "Evaluate another profile" }).click();
  await page.getByRole("button", { name: "Reset form" }).click();
  await expect(page.getByLabel("GPA on a 4.0 scale")).toHaveValue("3.6");
  expect(errors).toEqual([]);
});

test("advisor displays sources, names backend errors, and recovers on retry", async ({ page }) => {
  const errors = monitorErrors(page);
  let advisorFails = false;
  let recovered = false;

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) {
      await respond(route, health);
      return;
    }
    if (path.endsWith("/chat/ask")) {
      if (advisorFails) {
        await respond(route, { detail: "Document retrieval is unavailable." }, 503);
        return;
      }
      await respond(route, {
        answer: recovered ? "The advisor recovered successfully." : "The IELTS requirement is 7.0.",
        sources: [{ content_snippet: "Applicants must provide IELTS 7.0.", source_url: "https://example.edu/admissions", page: 12 }]
      });
      return;
    }
    await respond(route, { detail: "Unknown test endpoint." }, 404);
  });

  await page.goto("/advisor");
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();
  const question = page.getByRole("textbox", { name: "Question" });
  await question.fill("What IELTS result is required?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("The IELTS requirement is 7.0.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open source" })).toHaveAttribute("href", "https://example.edu/admissions");
  await expect(page.getByText("Page 12")).toBeVisible();

  advisorFails = true;
  await question.fill("Can you verify the deadline?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Document retrieval is unavailable.", { exact: true })).toBeVisible();

  advisorFails = false;
  recovered = true;
  await page.getByRole("button", { name: "Retry message" }).click();
  await expect(page.getByText("The advisor recovered successfully.")).toBeVisible();
  await expect(page.getByText("Can you verify the deadline?")).toHaveCount(1);
  expect(errors).toEqual([]);
});

test("application workflow loads, edits, copies, resets, reloads, and chats", async ({ page }) => {
  const errors = monitorErrors(page);
  let stateFails = false;

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) {
      await respond(route, health);
      return;
    }
    if (path.endsWith("/chat/agent/state")) {
      if (stateFails) {
        await respond(route, { detail: "Application state service unavailable." }, 503);
        return;
      }
      await respond(route, {
        student_id: "std_demo",
        target_program_id: "prog_101",
        application_stage: "gathering_info",
        missing_documents: ["official_transcript", "passport_copy", "motivation_letter"],
        drafted_motivation_letter: "Initial draft from backend."
      });
      return;
    }
    if (path.endsWith("/chat/agent")) {
      await respond(route, {
        response: "Agent prepared the draft.",
        student_id: "std_demo",
        application_stage: "drafting_documents",
        missing_documents: [],
        drafted_motivation_letter: "New draft from agent."
      });
      return;
    }
    await respond(route, { detail: "Unknown test endpoint." }, 404);
  });

  await page.goto("/application");
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(page.getByText("Initial draft from backend.")).toBeVisible();
  await expect(page.getByText("3 missing")).toBeVisible();
  await page.getByRole("button", { name: "Mark ready" }).first().click();
  await expect(page.getByText("2 missing")).toBeVisible();

  await page.getByRole("button", { name: "Copy draft" }).click();
  await expect(page.getByText("Draft copied to the clipboard.")).toBeVisible();
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe("Initial draft from backend.");

  await page.getByRole("button", { name: "Reset local demo" }).click();
  await expect(page.getByText("No draft is currently loaded.")).toBeVisible();
  await page.getByRole("button", { name: "Reload backend state" }).click();
  await expect(page.getByText("Initial draft from backend.")).toBeVisible();

  stateFails = true;
  await page.getByRole("button", { name: "Reload backend state" }).click();
  await expect(page.getByText(/Application state service unavailable\./)).toBeVisible();

  const message = page.getByRole("textbox", { name: "Message to the application agent" });
  await message.fill("Draft a motivation letter");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Agent prepared the draft.")).toBeVisible();
  await expect(page.getByText("New draft from agent.")).toBeVisible();
  await expect(page.getByText("All marked ready")).toBeVisible();
  await expect(page.getByText("drafting documents")).toBeVisible();
  expect(errors).toEqual([]);
});

test("registration validates locally and completes the existing account flow", async ({ page }) => {
  const errors = monitorErrors(page);
  let registrationPayload: Record<string, unknown> | null = null;

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) {
      await respond(route, health);
      return;
    }
    if (path.endsWith("/auth/register")) {
      registrationPayload = route.request().postDataJSON();
      await respond(route, { access_token: "test-token", token_type: "bearer" }, 201);
      return;
    }
    await respond(route, { detail: "Unknown test endpoint." }, 404);
  });
  await page.route("**/api/auth/callback/credentials", async (route) => {
    await respond(route, { url: "http://127.0.0.1:3100/match" });
  });

  await page.goto("/register");
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Email address").fill("new.student@example.com");
  await page.getByLabel("Password", { exact: true }).fill("secret1");
  await page.getByLabel("Confirm password").fill("secret2");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Passwords do not match", { exact: true })).toBeVisible();
  expect(registrationPayload).toBeNull();

  await page.getByLabel("Confirm password").fill("secret1");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/match$/);
  expect(registrationPayload).toMatchObject({
    email: "new.student@example.com",
    gpa: 3.5,
    degree_level: "master",
    country: "Azerbaijan"
  });
  expect(errors).toEqual([]);
});

test("sign-in reports rejected credentials and honors a safe callback after success", async ({ page }) => {
  const errors = monitorErrors(page);
  let accepted = false;
  await mockHealth(page);
  await page.route("**/api/auth/callback/credentials", async (route) => {
    const url = accepted
      ? "http://127.0.0.1:3100/application"
      : "http://127.0.0.1:3100/sign-in?error=CredentialsSignin";
    await respond(route, { url }, accepted ? 200 : 401);
  });

  await page.goto("/sign-in?callbackUrl=/application");
  await expect(page.locator("header").getByRole("link", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Email address").fill("student@example.com");
  await page.getByLabel("Password").fill("secret1");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText(/backend did not accept this sign-in attempt/)).toBeVisible();

  accepted = true;
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/application$/);
  expect(errors).toEqual([]);
});

test("compatibility redirect and missing route provide working exits", async ({ page }) => {
  const errors = monitorErrors(page);
  await mockHealth(page);
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/match$/);

  await page.goto("/route-that-does-not-exist");
  await expect(page.getByRole("heading", { name: "This route does not exist." })).toBeVisible();
  await page.getByRole("link", { name: "Return home" }).click();
  await expect(page).toHaveURL(/\/$/);
  expect(errors).toEqual([]);
});
