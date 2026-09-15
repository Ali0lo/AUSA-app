import type { RouteUniversity } from "@/types";
export function catalogueRow(changes: Partial<RouteUniversity> = {}): RouteUniversity {
  return { id: 1, university_name: "Test University", program_name: "Computing", country_code: "GB",
    level: "master", intake_year: 2026, entry_qualification_accepted: "bachelor_degree",
    foundation_required: null, foundation_providers: null, language_test: "IELTS", language_minimum_score: 7,
    entrance_exam: null, entrance_exam_minimum: null, gpa_minimum: null, gpa_scale: null,
    tuition_per_year: 10000, currency: "GBP", application_fee: null, application_deadline: "2026-03-27",
    application_portal: null, notes: "Relevant degree required", unknown_fields: ["gpa_minimum"],
    not_stated: "Grade minimum not recorded", grade_verdict: "no_minimum_published", grade_exact: false,
    grade_explanation: "Grade minimum unknown", provenance: "claude-extracted",
    source_url: "https://example.edu/admission", last_checked: "2026-09-15T00:00:00Z",
    checks: ["Deadline passed; check the next intake"], application_status: "deadline_passed",
    evidence: [{url: "https://example.edu/admission", fields: ["tuition_per_year"], checked_at: "2026-09-15", note: "Annual overseas fee"}], ...changes };
}
