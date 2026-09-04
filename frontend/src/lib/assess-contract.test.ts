/**
 * The frontend and backend must agree on the /routes/assess contract.
 *
 * `src/test/fixtures/assess-routes.json` is not hand-written. It is a real response,
 * captured from the FastAPI app running against the real curated file
 * (`data/curation/program_requirements_2026.csv`) for a real profile: an attestat holder
 * with 4.6 out of 5, IELTS 7.0 and a C1 certificate.
 *
 * That matters because `assessRoutes` validates every response and throws
 * "invalid-response" on anything that does not match. A hand-written fixture would only
 * prove the validator agrees with whoever wrote the fixture. This one fails if the backend
 * ever renames a field, drops one, or changes a type -- which is the actual way a typed
 * client and an untyped JSON API drift apart.
 *
 * Regenerate with the dump script if the endpoint's shape intentionally changes.
 */

import { describe, expect, it, vi, afterEach } from "vitest";
import { assessRoutes, ApiError } from "@/lib/api";
import fixture from "@/test/fixtures/assess-routes.json";

function mockFetchOnce(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      text: async () => JSON.stringify(body)
    })
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the /routes/assess contract", () => {
  it("accepts a response captured from the real backend", async () => {
    mockFetchOnce(fixture);
    const result = await assessRoutes({
      level_sought: "bachelor",
      qualification_held: "attestat"
    });

    expect(result.plans.length).toBeGreaterThan(0);
    expect(result.plans.flatMap((plan) => plan.universities).length).toBeGreaterThan(0);
  });

  it("carries the two-hop plan that reaches Cambridge and Manchester", async () => {
    mockFetchOnce(fixture);
    const result = await assessRoutes({
      level_sought: "bachelor",
      qualification_held: "attestat"
    });

    const prepYearToUk = result.plans.find(
      (plan) =>
        plan.hops.length === 2 &&
        plan.hops[0].key === "az-prep-year" &&
        plan.hops[1].key === "uk-bachelor-direct"
    );

    expect(prepYearToUk).toBeDefined();
    expect(prepYearToUk?.qualification_delivered).toBe("one_year_university");
    const names = prepYearToUk?.universities.map((u) => u.university_name) ?? [];
    expect(names).toContain("University of Cambridge");
    expect(names).toContain("University of Manchester");
    // The foundation-year universities belong to a different plan. If they appeared here
    // the join has regressed to keying on the destination country alone.
    expect(names).not.toContain("UCL");
  });

  it("carries a grade verdict on every university it returns", async () => {
    mockFetchOnce(fixture);
    const result = await assessRoutes({
      level_sought: "bachelor",
      qualification_held: "attestat"
    });

    for (const university of result.plans.flatMap((plan) => plan.universities)) {
      expect(typeof university.grade_verdict).toBe("string");
      expect(typeof university.grade_exact).toBe("boolean");
      // An exact verdict is only ever claimed for a real comparison, never for one of
      // the three non-answers.
      if (university.grade_exact) {
        expect(["meets", "below"]).toContain(university.grade_verdict);
      }
    }
  });

  it("explains every empty university list rather than leaving it bare", async () => {
    mockFetchOnce(fixture);
    const result = await assessRoutes({
      level_sought: "bachelor",
      qualification_held: "attestat"
    });

    for (const plan of result.plans) {
      if (plan.universities.length === 0) {
        expect(plan.universities_explanation.length).toBeGreaterThan(0);
        expect(plan.universities_status).not.toBe("listed");
      }
    }
  });

  it("rejects a response missing the grade_exact flag", async () => {
    // Not a hypothetical: dropping this field is exactly how a proportional cross-scale
    // comparison would silently start rendering as an exact one.
    const damaged = structuredClone(fixture) as typeof fixture;
    const target = damaged.plans.find((plan) => plan.universities.length > 0);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (target!.universities[0] as any).grade_exact;
    mockFetchOnce(damaged);

    await expect(
      assessRoutes({ level_sought: "bachelor", qualification_held: "attestat" })
    ).rejects.toThrow(ApiError);
  });

  it("rejects a response whose universities_explanation is missing", async () => {
    const damaged = structuredClone(fixture) as typeof fixture;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (damaged.plans[0] as any).universities_explanation;
    mockFetchOnce(damaged);

    await expect(
      assessRoutes({ level_sought: "bachelor", qualification_held: "attestat" })
    ).rejects.toThrow(ApiError);
  });

  it("omits a blank score from the request body rather than sending zero", async () => {
    mockFetchOnce(fixture);
    await assessRoutes({
      level_sought: "bachelor",
      qualification_held: "attestat",
      ielts: 7,
      toefl: null,
      sat: undefined
    });

    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse((call[1] as RequestInit).body as string);
    expect(body.ielts).toBe(7);
    expect("toefl" in body).toBe(false);
    expect("sat" in body).toBe(false);
  });
});
