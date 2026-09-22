import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AdmissionsTimeline } from "./AdmissionsTimeline";

describe("AdmissionsTimeline Component", () => {
  beforeEach(() => {
    window.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    window.URL.revokeObjectURL = vi.fn();
  });

  it("renders hero header, statistics summary, and action buttons", () => {
    render(<AdmissionsTimeline />);
    expect(screen.getByText(/Qəbul & Təqaüd Dedlayn İzləyicisi/i)).toBeInTheDocument();
    expect(screen.getByText(/Bütün Dedlaynları Təqvimə Yazdır \(\.ics\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Fərdi Dedlayn Əlavə Et/i)).toBeInTheDocument();
    expect(screen.getByText(/Ümumi Tarixlər/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Təcili/i).length).toBeGreaterThan(0);
  });

  it("filters milestones when a country filter pill is clicked", () => {
    render(<AdmissionsTimeline />);
    const ukPill = screen.getByRole("button", { name: /Böyük Britaniya/i });
    fireEvent.click(ukPill);

    // UK milestones should be visible (using getAllByText because it may appear in top banner and timeline)
    expect(screen.getAllByText(/UCAS Oxbridge, Medicine & Dentistry Early Deadline/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/UK Chevening Master's Scholarship Deadline/i).length).toBeGreaterThan(0);

    // Germany or US milestone should not be shown
    expect(screen.queryByText(/US Common App Early Action/i)).not.toBeInTheDocument();
  });

  it("filters by State Programme eligibility checkbox", () => {
    render(<AdmissionsTimeline />);
    const dpCheckbox = screen.getByLabelText(/Yalnız Dövlət Proqramına Uyğun/i);
    fireEvent.click(dpCheckbox);

    // Should contain DP eligible milestone
    expect(screen.getByText(/State Programme 2022–2026 \(DP\) Portal Opens/i)).toBeInTheDocument();
  });

  it("filters milestones using the search input", () => {
    render(<AdmissionsTimeline />);
    const searchInput = screen.getByPlaceholderText(/Portal, universitet, şəhər və ya imtahan axtar/i);
    fireEvent.change(searchInput, { target: { value: "Uni-Assist" } });

    expect(screen.getAllByText(/Germany Winter Semester \(Wintersemester\) Uni-Assist/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/UCAS Oxbridge/i)).not.toBeInTheDocument();
  });

  it("opens custom deadline modal, enters details, and creates a reminder", async () => {
    render(<AdmissionsTimeline />);
    const customBtn = screen.getByRole("button", { name: /Fərdi Dedlayn Əlavə Et/i });
    fireEvent.click(customBtn);

    expect(screen.getByText(/Fərdi Universitet Dedlaynı Əlavə Et/i)).toBeInTheDocument();

    const titleInput = screen.getByPlaceholderText(/TUM Informatiik Motivasiya Məktubu Son Tarixi/i);
    fireEvent.change(titleInput, { target: { value: "TUM Master Application" } });

    // Fill the required date input
    const dateInput = document.querySelector('input[type="date"]') as HTMLInputElement;
    expect(dateInput).not.toBeNull();
    fireEvent.change(dateInput, { target: { value: "2026-10-25" } });

    const submitBtn = screen.getByRole("button", { name: /Təqvim Faylını Yarat \(\.ics\)/i });
    fireEvent.click(submitBtn);

    // Modal closes upon submit
    await waitFor(() => {
      expect(screen.queryByText(/Fərdi Universitet Dedlaynı Əlavə Et/i)).not.toBeInTheDocument();
    });

    expect(window.URL.createObjectURL).toHaveBeenCalled();
  });

  it("triggers calendar download when export all button is clicked", () => {
    render(<AdmissionsTimeline />);
    const exportBtn = screen.getByRole("button", { name: /Bütün Dedlaynları Təqvimə Yazdır \(\.ics\)/i });
    fireEvent.click(exportBtn);

    expect(window.URL.createObjectURL).toHaveBeenCalled();
  });
});
