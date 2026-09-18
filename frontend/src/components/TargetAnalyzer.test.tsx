import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TargetAnalyzer } from "./TargetAnalyzer";
import { assessTargetGap, fetchTargetCatalog } from "@/lib/api";
import type { TargetCatalogItem, TargetGapResponse } from "@/types";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    fetchTargetCatalog: vi.fn(),
    assessTargetGap: vi.fn()
  };
});

const mockCatalog: TargetCatalogItem[] = [
  {
    university_name: "Technical University of Munich",
    program_name: "Informatics B.Sc.",
    level: "bachelor",
    country_code: "DE",
    source_type: "curated",
    source_url: "https://www.tum.de"
  },
  {
    university_name: "Middle East Technical University",
    program_name: "Computer Engineering B.Sc.",
    level: "bachelor",
    country_code: "TR",
    source_type: "curated",
    source_url: "https://www.metu.edu.tr"
  }
];

const mockCuratedResponse: TargetGapResponse = {
  found: true,
  university_name: "Technical University of Munich",
  program_name: "Informatics B.Sc.",
  level: "bachelor",
  country_code: "DE",
  route_status: "UNLOCKABLE",
  route_gap_statement:
    "Azerbaijani 11-year Attestat requires a Studienkolleg prep course (T-Kurs) or 1 year of university study before direct entry.",
  unlock_steps: [
    "Complete Studienkolleg (T-Kurs) or 1 year accredited university in Azerbaijan",
    "Pass Feststellungsprüfung (FSP) with required math/physics components"
  ],
  unlock_time_months: 12,
  unlock_cost_azn_low: 15000,
  unlock_cost_azn_high: 25000,
  checklist: [
    {
      name: "Qualification Recognition",
      requirement: "12-year equivalent or Studienkolleg",
      student_value: "attestat",
      status: "GAP",
      explanation: "Attestat requires prep course"
    },
    {
      name: "Language Proficiency",
      requirement: "German C1 or English IELTS 6.5",
      student_value: "IELTS 7.0",
      status: "MET",
      explanation: "Meets stated language bar"
    },
    {
      name: "Entrance Exam",
      requirement: "TestAS or internal assessment",
      student_value: null,
      status: "UNKNOWN",
      explanation: "TestAS score not entered"
    }
  ],
  application_portal: "TUMonline",
  application_deadline: "July 15",
  application_fee: 0,
  currency: "EUR",
  documents_required: "Attestat transcript, uni-assist VPD, Proof of language proficiency",
  alternatives: [
    {
      university_name: "Middle East Technical University",
      country_code: "TR",
      reason: "Direct bachelor entry with Attestat and DİM/SAT without Studienkolleg"
    }
  ],
  provenance: "human-verified",
  source_url: "https://www.tum.de/en/studies/degree-programs/detail/informatics-bachelor-of-science-bsc",
  last_checked: "2026-09-01T00:00:00Z"
};

const mockUncuratedResponse: TargetGapResponse = {
  found: false,
  university_name: "University of Bologna",
  program_name: "Undergraduate Studies",
  level: "bachelor",
  country_code: "IT",
  route_status: "UNKNOWN",
  route_gap_statement:
    "Requirements for University of Bologna have not been curated in our database yet. This is a catalogue gap in our data, not a statement that the institution will reject you. Please consult the university's official admissions office or portal for verified entry criteria.",
  unlock_steps: [],
  unlock_time_months: 0,
  unlock_cost_azn_low: 0,
  unlock_cost_azn_high: 0,
  checklist: [
    {
      name: "Institutional Requirements",
      requirement: "Uncurated institution",
      student_value: null,
      status: "UNKNOWN",
      explanation: "Requirements have not been verified in the AUSA catalogue yet"
    }
  ],
  application_portal: null,
  application_deadline: null,
  application_fee: null,
  currency: null,
  documents_required: null,
  alternatives: [],
  provenance: "claude-extracted",
  source_url: "",
  last_checked: null
};

describe("TargetAnalyzer Component", () => {
  beforeEach(() => {
    vi.mocked(fetchTargetCatalog).mockReset().mockResolvedValue(mockCatalog);
    vi.mocked(assessTargetGap).mockReset().mockResolvedValue(mockCuratedResponse);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the initial form with catalog quick picks and controls", async () => {
    render(<TargetAnalyzer />);
    expect(screen.getByRole("heading", { name: /Target University Analyzer/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Target University/i)).toBeInTheDocument();

    expect(await screen.findByRole("button", { name: "Technical University of Munich" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Middle East Technical University" })).toBeInTheDocument();
  });

  it("analyzes target university and renders gap analysis, checklist, process milestones, and alternatives", async () => {
    const user = userEvent.setup();
    render(<TargetAnalyzer />);

    const input = screen.getByLabelText(/Target University/i);
    await user.clear(input);
    await user.type(input, "Technical University of Munich");

    const analyzeBtn = screen.getByRole("button", { name: /Analyze Target Gap/i });
    await user.click(analyzeBtn);

    await waitFor(() => {
      expect(assessTargetGap).toHaveBeenCalledWith(
        expect.objectContaining({
          university_name: "Technical University of Munich",
          level: "bachelor"
        })
      );
    });

    // 1. Route Gap Statement
    expect(await screen.findByRole("heading", { name: /1\. Objective Gap Statement/i })).toBeInTheDocument();
    expect(screen.getByText(/Studienkolleg prep course/i)).toBeInTheDocument();
    expect(screen.getByText(/Route Unlockable via Bridge/i)).toBeInTheDocument();
    expect(screen.getAllByText(/12 months/i).length).toBeGreaterThanOrEqual(1);

    // 2. Requirement Checklist
    expect(screen.getByRole("heading", { name: /2\. Requirement Checklist/i })).toBeInTheDocument();
    expect(screen.getByText(/Qualification Recognition/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Language Proficiency" })).toBeInTheDocument();
    expect(screen.getByText(/✓ Met/i)).toBeInTheDocument();
    expect(screen.getByText(/⚠ Gap/i)).toBeInTheDocument();

    // 3. Process Milestones & Deadlines
    expect(screen.getByRole("heading", { name: /3\. Process Milestones & Deadlines/i })).toBeInTheDocument();
    expect(screen.getAllByText(/July 15/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/TUMonline/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Mandatory Execution Milestones/i)).toBeInTheDocument();

    // 4. Viable Alternatives
    expect(screen.getByRole("heading", { name: /4\. Viable Alternatives Closing the Gap/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Middle East Technical University" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Target This Alternative/i })).toBeInTheDocument();
  });

  it("handles uncurated university with honest catalogue gap message and excludes speculative study plans", async () => {
    vi.mocked(assessTargetGap).mockResolvedValueOnce(mockUncuratedResponse);

    const user = userEvent.setup();
    render(<TargetAnalyzer initialUniversity="University of Bologna" />);

    await waitFor(() => {
      expect(assessTargetGap).toHaveBeenCalledWith(
        expect.objectContaining({ university_name: "University of Bologna" })
      );
    });

    // Honest catalogue gap banner
    expect(
      await screen.findByRole("heading", { name: /Catalogue Gap \(Our Data, Not an Admission Rejection\)/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/have not been collected or verified in the AUSA catalogue yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Speculative study plans excluded:/i)).toBeInTheDocument();
  });

  it("allows selecting an alternative university and re-assesses target gap", async () => {
    const user = userEvent.setup();
    render(<TargetAnalyzer initialUniversity="Technical University of Munich" />);

    await waitFor(() => expect(assessTargetGap).toHaveBeenCalledTimes(1));

    const altButton = await screen.findByRole("button", { name: /Target This Alternative/i });
    await user.click(altButton);

    await waitFor(() => {
      expect(assessTargetGap).toHaveBeenCalledWith(
        expect.objectContaining({
          university_name: "Middle East Technical University"
        })
      );
    });
  });

  it("renders user-friendly error message when assessment fails", async () => {
    vi.mocked(assessTargetGap).mockRejectedValueOnce(new Error("Network connection lost"));

    const user = userEvent.setup();
    render(<TargetAnalyzer />);

    const input = screen.getByLabelText(/Target University/i);
    await user.type(input, "Oxford");

    const analyzeBtn = screen.getByRole("button", { name: /Analyze Target Gap/i });
    await user.click(analyzeBtn);

    expect(await screen.findByText(/Unable to assess target/i)).toBeInTheDocument();
  });
});
