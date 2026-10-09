import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApplicationTracker } from "@/components/ApplicationTracker";
import { TrackedApplication } from "@/types";

const TUM: TrackedApplication = {
  id: 1,
  student_id: "5",
  university_name: "Technical University of Munich",
  program_name: "Informatics BSc",
  country: "Germany",
  deadline: "2026-12-15",
  stage: "shortlisted",
  days_remaining: 67,
  is_urgent: false
};

describe("ApplicationTracker", () => {
  it("shows applications that arrive after it first rendered", () => {
    // The page renders the tracker before its fetch resolves, so the first list is empty.
    const { rerender } = render(<ApplicationTracker initialApplications={[]} />);
    expect(screen.queryByText("Technical University of Munich")).not.toBeInTheDocument();

    rerender(<ApplicationTracker initialApplications={[TUM]} />);

    expect(screen.getByText("Technical University of Munich")).toBeInTheDocument();
  });
});
