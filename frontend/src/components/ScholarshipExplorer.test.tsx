import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ScholarshipExplorer } from "./ScholarshipExplorer";

describe("ScholarshipExplorer Component", () => {
  it("renders page title and global scholarships hub badge", () => {
    render(<ScholarshipExplorer />);
    expect(screen.getByText(/Global & Bilateral Scholarships Hub/i)).toBeInTheDocument();
    expect(screen.getByText(/Comprehensive Global Scholarship Engine/i)).toBeInTheDocument();
  });

  it("renders all 14 global scholarships by default", () => {
    render(<ScholarshipExplorer />);
    expect(screen.getByText(/Showing 14 of 14 scholarships/i)).toBeInTheDocument();
    expect(screen.getByText(/Chevening Scholarship/i)).toBeInTheDocument();
    expect(screen.getByText(/Fulbright Foreign Student Program/i)).toBeInTheDocument();
    expect(screen.getByText(/Türkiye Bursları/i)).toBeInTheDocument();
    expect(screen.getByText(/Stipendium Hungaricum/i)).toBeInTheDocument();
    expect(screen.getByText(/Italian Regional DSU Scholarships/i)).toBeInTheDocument();
  });

  it("filters scholarships by country chip", () => {
    render(<ScholarshipExplorer />);
    const ukChip = screen.getByRole("button", { name: /UK/i });
    fireEvent.click(ukChip);

    expect(screen.getByText(/Chevening Scholarship/i)).toBeInTheDocument();
    expect(screen.getByText(/GREAT Scholarships/i)).toBeInTheDocument();
    // Non-UK should be filtered out
    expect(screen.queryByText(/Stipendium Hungaricum/i)).not.toBeInTheDocument();
  });

  it("filters scholarships by degree level", () => {
    render(<ScholarshipExplorer />);
    const degreeSelect = screen.getByDisplayValue("All Degree Levels");
    fireEvent.change(degreeSelect, { target: { value: "bachelor" } });

    // Should include Türkiye Bursları and Stipendium Hungaricum
    expect(screen.getByText(/Türkiye Bursları/i)).toBeInTheDocument();
    expect(screen.getByText(/Stipendium Hungaricum/i)).toBeInTheDocument();
    // Chevening is Master only
    expect(screen.queryByText(/Chevening Scholarship/i)).not.toBeInTheDocument();
  });

  it("filters scholarships by search query", () => {
    render(<ScholarshipExplorer />);
    const searchInput = screen.getByPlaceholderText(/Search by scholarship name/i);
    fireEvent.change(searchInput, { target: { value: "Eiffel" } });

    expect(screen.getByText(/Eiffel Excellence Scholarship/i)).toBeInTheDocument();
    expect(screen.queryByText(/Fulbright Foreign Student/i)).not.toBeInTheDocument();
  });

  it("opens and closes detailed dossier modal", () => {
    render(<ScholarshipExplorer />);
    const viewButtons = screen.getAllByRole("button", { name: /View Dossier/i });
    fireEvent.click(viewButtons[0]);

    expect(screen.getByText(/Full Funding Coverage/i)).toBeInTheDocument();
    expect(screen.getByText(/Key Statutory Eligibility Criteria/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open Official Application Portal/i })).toBeInTheDocument();

    const closeButton = screen.getByLabelText("Close modal");
    fireEvent.click(closeButton);

    expect(screen.queryByText(/Full Funding Coverage/i)).not.toBeInTheDocument();
  });

  it("toggles eligibility checker drawer and displays qualification statuses", () => {
    render(<ScholarshipExplorer />);
    const assessButton = screen.getByRole("button", { name: /Assess My Eligibility/i });
    fireEvent.click(assessButton);

    expect(screen.getByText(/Student Profile Eligibility Evaluator/i)).toBeInTheDocument();
    expect(screen.getByText(/Degree Level Sought/i)).toBeInTheDocument();
    expect(screen.getByText(/Profile filter active/i)).toBeInTheDocument();

    // Verify OPEN, UNLOCKABLE, and BLOCKED status pills appear
    expect(screen.getByRole("button", { name: /OPEN/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /UNLOCKABLE/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /BLOCKED/i })).toBeInTheDocument();
  });
});
