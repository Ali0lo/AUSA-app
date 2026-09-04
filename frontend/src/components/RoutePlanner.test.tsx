import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RoutePlanner } from "@/components/RoutePlanner";
import type { AssessRoutesResponse, RouteUniversity, Scholarship } from "@/types";

const assessRoutes = vi.fn();
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, assessRoutes: (...args: unknown[]) => assessRoutes(...args) };
});

function university(overrides: Partial<RouteUniversity> = {}): RouteUniversity {
  return {
    university_name: "University of Manchester",
    program_name: "International undergraduate admission",
    country_code: "GB",
    intake_year: 2026,
    entry_qualification_accepted: "one_year_university",
    foundation_required: false,
    foundation_providers: null,
    language_test: null,
    language_minimum_score: null,
    entrance_exam: null,
    entrance_exam_minimum: null,
    gpa_minimum: null,
    gpa_scale: null,
    tuition_per_year: null,
    currency: null,
    application_fee: null,
    application_deadline: null,
    application_portal: "UCAS",
    notes: null,
    unknown_fields: ["tuition_per_year", "language_test"],
    not_stated:
      "Not stated on the source page, so not recorded: tuition per year, language test. " +
      "Unknown here means we could not find it, never that it is not required.",
    grade_verdict: "no_minimum_published",
    grade_exact: false,
    grade_explanation: "This university's page does not state a minimum grade.",
    provenance: "claude-extracted",
    source_url: "https://www.manchester.ac.uk/azerbaijan",
    last_checked: "2026-09-02T00:00:00Z",
    ...overrides
  };
}

function scholarship(overrides: Partial<Scholarship> = {}): Scholarship {
  return {
    key: "turkiye-burslari",
    name: "Türkiye Bursları",
    provider: "Government of Türkiye",
    tier: 2,
    country_code: "TR",
    coverage: "Fully funded: tuition waiver, monthly stipend, dormitory and health insurance",
    status: "open",
    gates_met: ["You are 19, under the age limit of 21"],
    gates_missing: [],
    gates_blocked: [],
    gates_unknown: [],
    obligation: null,
    window: "Applications run 10 January to 20 February.",
    citation: "spec §5.2",
    provenance: "research-brief",
    ...overrides
  };
}

function response(overrides: Partial<AssessRoutesResponse> = {}): AssessRoutesResponse {
  return {
    blocked: [],
    scholarships: [scholarship()],
    scholarships_note:
      "Meeting an award's published gates makes you possibly eligible to apply. It is never an award.",
    prep_year_warning: null,
    plans: [
      {
        hops: [
          {
            key: "az-prep-year",
            country_code: "AZ",
            mechanism: "One year of study at a recognised Azerbaijani university",
            time_cost_months: 12,
            money_cost_azn_low: 0,
            money_cost_azn_high: 4000,
            citation: "uni-assist",
            provenance: "seed"
          },
          {
            key: "uk-bachelor-direct",
            country_code: "GB",
            mechanism: "Direct entry via UCAS",
            time_cost_months: 0,
            money_cost_azn_low: 30000,
            money_cost_azn_high: 70000,
            citation: "UK ENIC",
            provenance: "seed"
          }
        ],
        total_months: 12,
        total_cost_azn_low: 30000,
        total_cost_azn_high: 74000,
        status: "unlockable",
        missing: ["IELTS required, minimum 6.5"],
        destination_country: "GB",
        qualification_delivered: "one_year_university",
        universities: [university()],
        universities_status: "listed",
        universities_explanation: ""
      }
    ],
    dp: {
      status: "unlockable",
      band_checked: "DİM 400-550",
      gates_met: [],
      gates_missing: ["A language certificate at C1 or above is required"],
      note: "Meeting these published requirements makes you possibly eligible to apply.",
      funded_programmes: [],
      funded_programmes_status: "dp_programmes_exist_but_not_in_a_reachable_country",
      funded_programmes_explanation: "The Dövlət Proqramı funds programmes at this level, but not in a country your current profile can reach."
    },
    ...overrides
  };
}

async function submitForm() {
  await userEvent.click(screen.getByRole("button", { name: /show my options/i }));
}

beforeEach(() => {
  assessRoutes.mockReset();
});

describe("RoutePlanner", () => {
  it("sends a blank score as absent rather than as zero", async () => {
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);

    await userEvent.type(screen.getByLabelText(/IELTS/i), "7");
    await submitForm();

    await waitFor(() => expect(assessRoutes).toHaveBeenCalled());
    const payload = assessRoutes.mock.calls[0][0];
    expect(payload.ielts).toBe(7);
    // "Did not sit the exam" and "scored zero" are different facts. A 0 here would
    // be a score the student never claimed.
    expect(payload.toefl).toBeUndefined();
    expect(payload.sat).toBeUndefined();
    expect(payload.dim_score).toBeUndefined();
  });

  it("does not send a grade scale when no grade was entered", async () => {
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);
    await submitForm();

    await waitFor(() => expect(assessRoutes).toHaveBeenCalled());
    const payload = assessRoutes.mock.calls[0][0];
    expect(payload.gpa).toBeUndefined();
    expect(payload.gpa_scale).toBeUndefined();
  });

  it("sends the grade together with the scale it is on", async () => {
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);

    await userEvent.type(screen.getByLabelText(/grade average/i), "4.6");
    await submitForm();

    await waitFor(() => expect(assessRoutes).toHaveBeenCalled());
    const payload = assessRoutes.mock.calls[0][0];
    expect(payload.gpa).toBe(4.6);
    expect(payload.gpa_scale).toBe("5.0");
  });

  it("names what a university's page did not state", async () => {
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);
    await submitForm();

    expect(await screen.findByText(/never that it is not required/i)).toBeInTheDocument();
  });

  it("marks a cross-scale grade comparison as rough rather than exact", async () => {
    assessRoutes.mockResolvedValue(
      response({
        plans: [
          {
            ...response().plans[0],
            universities: [
              university({
                grade_verdict: "meets",
                grade_exact: false,
                grade_explanation: "Compared proportionally, 92% against 80%.",
                gpa_minimum: 80,
                gpa_scale: "100"
              })
            ]
          }
        ]
      })
    );
    render(<RoutePlanner />);
    await submitForm();

    expect(await screen.findByText(/Appears to clear the minimum/i)).toBeInTheDocument();
    expect(screen.getByText(/not an official conversion/i)).toBeInTheDocument();
  });

  it("states an exact grade comparison without the rough-comparison caveat", async () => {
    assessRoutes.mockResolvedValue(
      response({
        plans: [
          {
            ...response().plans[0],
            universities: [
              university({
                university_name: "UCL",
                grade_verdict: "meets",
                grade_exact: true,
                grade_explanation: "Your 4.8 clears the stated minimum of 4.5.",
                gpa_minimum: 4.5,
                gpa_scale: "5.0"
              })
            ]
          }
        ]
      })
    );
    render(<RoutePlanner />);
    await submitForm();

    // An exact string rather than a regex: the backend's own explanation repeats the
    // phrase ("Your 4.8 clears the stated minimum of 4.5"), so a loose match finds two
    // elements and tells us nothing about which one rendered.
    expect(await screen.findByText("Clears the stated minimum")).toBeInTheDocument();
    // The point of the test: an exact comparison must NOT carry the caveat that a
    // proportional one does, or the caveat stops meaning anything.
    expect(screen.queryByText(/not an official conversion/i)).not.toBeInTheDocument();
  });

  it("explains an empty university list instead of showing nothing", async () => {
    assessRoutes.mockResolvedValue(
      response({
        plans: [
          {
            ...response().plans[0],
            universities: [],
            universities_status: "no_requirements_collected_for_this_country_yet",
            universities_explanation:
              "We have not collected university requirements for GB yet. This is a gap in our data, not a statement that no university there accepts you."
          }
        ]
      })
    );
    render(<RoutePlanner />);
    await submitForm();

    // The empty list must never be left to speak for itself: a student would read
    // it as "nowhere will take me".
    expect(await screen.findByText(/gap in our data/i)).toBeInTheDocument();
  });

  it("says eligibility is not an award for every funder, not just the state programme", async () => {
    // The rule is spec §5.2's and it binds the whole funding section: "possibly eligible",
    // never "you will get it". Two notices carry it now -- the DP panel and the
    // scholarship list -- and both have to, because a student reads whichever one their
    // own funding hopes are in.
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);
    await submitForm();

    const notices = await screen.findAllByText(/possibly eligible to apply/i);
    expect(notices).toHaveLength(2);
  });

  it("says why a scholarship is closed rather than dropping it from the page", async () => {
    // A 22-year-old who simply does not see Türkiye Bursları will apply for it anyway in
    // January. The blocked award has to be on the page, with the gate that closed it.
    assessRoutes.mockResolvedValue(
      response({
        scholarships: [
          scholarship({
            status: "blocked",
            gates_met: [],
            gates_blocked: [
              "You are 22 and this award requires you to be under 21 at bachelor level."
            ]
          })
        ]
      })
    );
    render(<RoutePlanner />);
    await submitForm();

    expect(await screen.findByText(/Closed to you/i)).toBeInTheDocument();
    expect(screen.getByText(/requires you to be under 21/i)).toBeInTheDocument();
  });

  it("labels a gate it could not check instead of folding it in with the missing ones", async () => {
    // The two ask different things of the student: one is work to do, the other is a fact
    // to tell us. Merged, we would be telling them to act on a question we never asked.
    assessRoutes.mockResolvedValue(
      response({
        scholarships: [
          scholarship({
            status: "unlockable",
            gates_met: [],
            gates_unknown: [
              "This award requires you to be under 21 at bachelor level. Tell us your age and this becomes a definite answer either way"
            ]
          })
        ]
      })
    );
    render(<RoutePlanner />);
    await submitForm();

    expect(await screen.findByText(/What we could not check/i)).toBeInTheDocument();
    expect(screen.getByText(/Tell us your age/i)).toBeInTheDocument();
  });

  it("surfaces the prep-year trade-off when the backend reports one", async () => {
    assessRoutes.mockResolvedValue(
      response({
        prep_year_warning:
          "Taking the 12-month prep year would make you 21 at the next Türkiye Bursları window, which is at or over its under-21 bachelor limit."
      })
    );
    render(<RoutePlanner />);
    await submitForm();

    expect(await screen.findByText(/One route costs you another option/i)).toBeInTheDocument();
    expect(screen.getByText(/under-21 bachelor limit/i)).toBeInTheDocument();
  });

  it("does not invent a trade-off when the backend reports none", async () => {
    assessRoutes.mockResolvedValue(response({ prep_year_warning: null }));
    render(<RoutePlanner />);
    await submitForm();

    await screen.findByText(/routes, soonest first/i);
    expect(screen.queryByText(/One route costs you another option/i)).not.toBeInTheDocument();
  });

  it("asks for an employer only where an award is actually gated on one", async () => {
    // SOCAR's scholarship is master's-only, so a school-leaver is never asked who they
    // work for. Asking anyway reads as profiling and gets left blank.
    render(<RoutePlanner />);

    expect(screen.queryByLabelText(/^Employer$/i)).not.toBeInTheDocument();

    await userEvent.selectOptions(
      screen.getByLabelText(/I am applying for/i),
      "master"
    );

    expect(screen.getByLabelText(/^Employer$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Documented work experience/i)).toBeInTheDocument();
  });

  it("sends age, hours and employer so the funding gates can be checked", async () => {
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);

    await userEvent.selectOptions(screen.getByLabelText(/I am applying for/i), "master");
    await userEvent.type(screen.getByLabelText(/^Age$/i), "24");
    await userEvent.type(screen.getByLabelText(/Documented work experience/i), "3000");
    await userEvent.type(screen.getByLabelText(/^Employer$/i), "SOCAR");
    await submitForm();

    await waitFor(() => expect(assessRoutes).toHaveBeenCalled());
    const payload = assessRoutes.mock.calls[0][0];
    expect(payload.age).toBe(24);
    expect(payload.work_experience_hours).toBe(3000);
    expect(payload.employer).toBe("SOCAR");
  });

  it("treats a blank age as unknown rather than as zero", async () => {
    assessRoutes.mockResolvedValue(response());
    render(<RoutePlanner />);
    await submitForm();

    await waitFor(() => expect(assessRoutes).toHaveBeenCalled());
    const payload = assessRoutes.mock.calls[0][0];
    expect(payload.age).toBeUndefined();
    expect(payload.employer).toBeUndefined();
  });

  it("reports a backend failure instead of rendering an empty result", async () => {
    assessRoutes.mockRejectedValue(new Error("boom"));
    render(<RoutePlanner />);
    await submitForm();

    expect(await screen.findByText(/Unexpected error/i)).toBeInTheDocument();
    expect(screen.queryByText(/routes, soonest first/i)).not.toBeInTheDocument();
  });
});
