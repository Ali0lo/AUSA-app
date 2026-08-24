import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MatchCard } from "@/components/MatchCard";
import type { MatchResult } from "@/types";

const result: MatchResult = {
  program_name: "BSc Data Science",
  university_name: "University College London (UCL)",
  overall_match_percentage: 72.4,
  is_eligible: false,
  ineligibility_reasons: ["Degree level does not match."],
  breakdown: {
    degree_level: { score: 0, weight: 0.2, weighted_score: 0, passed_hard_filter: false, explanation: "Master and bachelor differ." },
    academic: { score: 100, weight: 0.3, weighted_score: 30, passed_hard_filter: true, explanation: "GPA passes." },
    budget: { score: 60, weight: 0.3, weighted_score: 18, passed_hard_filter: false, explanation: "Budget is below tuition." },
    language: { score: 100, weight: 0.2, weighted_score: 20, passed_hard_filter: true, explanation: "Language passes." }
  }
};

describe("MatchCard", () => {
  it("renders the full backend breakdown and reset action", async () => {
    const user = userEvent.setup();
    const reset = vi.fn();
    render(<MatchCard result={result} onReset={reset} />);

    expect(screen.getByRole("heading", { name: "BSc Data Science" })).toBeInTheDocument();
    expect(screen.getByText("72%")).toBeInTheDocument();
    expect(screen.getByText("Degree level does not match.")).toBeInTheDocument();
    expect(screen.getAllByText("Passed")).toHaveLength(2);
    expect(screen.getAllByText("Did not pass")).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: "Evaluate another profile" }));
    expect(reset).toHaveBeenCalledOnce();
  });
});
