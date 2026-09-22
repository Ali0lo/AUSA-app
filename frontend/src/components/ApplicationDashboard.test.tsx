import { describe, expect, it, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ApplicationDashboard } from "./ApplicationDashboard";
import { ComparisonMatrix } from "./ComparisonMatrix";

describe("ApplicationDashboard Component", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders hero banner, stats summary, and action triggers", () => {
    render(<ApplicationDashboard />);

    expect(screen.getByText(/Tələbə Müraciət İdarəetmə Paneli/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Universitetləri Müqayisə Et/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Yeni Müraciət Əlavə Et/i })).toBeInTheDocument();

    // Check stats boxes
    expect(screen.getByText(/Cəmi Müraciətlər/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Dream \(Xəyal\)/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Target \(Hədəf\)/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Safety \(Təhlükəsiz\)/i).length).toBeGreaterThan(0);
  });

  it("renders seeded benchmark applications initially", () => {
    render(<ApplicationDashboard />);

    // TUM, Politecnico di Milano, ITU are in DEFAULT_APPLICATIONS
    expect(screen.getAllByText(/Technical University of Munich/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Politecnico di Milano/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Istanbul Technical University/i).length).toBeGreaterThan(0);
  });

  it("filters applications by tier tabs (DREAM, TARGET, SAFETY)", () => {
    render(<ApplicationDashboard />);

    // Click DREAM filter
    const dreamTab = screen.getByRole("button", { name: /Dream \(/i });
    fireEvent.click(dreamTab);

    // TUM is DREAM
    expect(screen.getAllByText(/Technical University of Munich/i).length).toBeGreaterThan(0);
    // PoliMi is TARGET, should not be visible in filtered list
    expect(screen.queryByText(/Politecnico di Milano/i)).not.toBeInTheDocument();

    // Click TARGET filter
    const targetTab = screen.getByRole("button", { name: /Target \(/i });
    fireEvent.click(targetTab);
    expect(screen.getAllByText(/Politecnico di Milano/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Technical University of Munich/i)).not.toBeInTheDocument();

    // Click All filter
    const allTab = screen.getByRole("button", { name: /Hamısı \(/i });
    fireEvent.click(allTab);
    expect(screen.getAllByText(/Technical University of Munich/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Politecnico di Milano/i).length).toBeGreaterThan(0);
  });

  it("opens document checklist modal and toggles a document", () => {
    render(<ApplicationDashboard />);

    // Click first "Sənədlər" button
    const docButtons = screen.getAllByRole("button", { name: /Sənədlər/i });
    expect(docButtons.length).toBeGreaterThan(0);
    fireEvent.click(docButtons[0]);

    // Modal should be open
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Ümumi İcra Vəziyyəti/i)).toBeInTheDocument();

    // Find and toggle a document item
    const passportItem = screen.getAllByText(/Xarici Pasport/i)[0];
    expect(passportItem).toBeInTheDocument();
    fireEvent.click(passportItem);

    // Close modal
    const closeBtn = screen.getByRole("button", { name: /Yadda Saxla & Bağla/i });
    fireEvent.click(closeBtn);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens university comparison modal when clicking comparison button", () => {
    render(<ApplicationDashboard />);

    const compareBtn = screen.getByRole("button", { name: /Universitetləri Müqayisə Et/i });
    fireEvent.click(compareBtn);

    // Comparison modal should be displayed
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Çoxölçülü Müqayisə Matrisi/i)).toBeInTheDocument();
    expect(screen.getByText(/Universitetlərin Müqayisəsi & Xərc\/Viza Təhlili/i)).toBeInTheDocument();
    expect(screen.getByText(/Ən Sərfəli Seçim/i)).toBeInTheDocument();
    expect(screen.getByText(/Ən Uzun İş Vizası/i)).toBeInTheDocument();

    // Close modal using first close button
    const closeButtons = screen.getAllByRole("button", { name: /Bağla/i });
    expect(closeButtons.length).toBeGreaterThan(0);
    fireEvent.click(closeButtons[0]);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("adds a new benchmark application via the modal", () => {
    render(<ApplicationDashboard />);

    const addBtn = screen.getByRole("button", { name: /Yeni Müraciət Əlavə Et/i });
    fireEvent.click(addBtn);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Yeni Universitet Müraciəti Əlavə Et/i)).toBeInTheDocument();

    // Select Oxford from benchmark dropdown using aria-label
    const select = screen.getByLabelText(/Hazır Benchmark Universitetlər/i);
    fireEvent.change(select, { target: { value: "oxford_cs" } });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /Müraciəti Əlavə Et/i });
    fireEvent.click(submitBtn);

    // Oxford should now appear in the list
    expect(screen.getAllByText(/University of Oxford/i).length).toBeGreaterThan(0);
  });

  it("deletes an application when trash icon is clicked", () => {
    render(<ApplicationDashboard />);

    const deleteButtons = screen.getAllByLabelText(/Müraciəti sil/i);
    expect(deleteButtons.length).toBeGreaterThan(0);
    fireEvent.click(deleteButtons[0]);

    // One application was removed
    expect(screen.queryByText(/Technical University of Munich \(TUM\)/i)).not.toBeInTheDocument();
  });
});

describe("ComparisonMatrix Standalone Component", () => {
  it("renders side-by-side comparison table for benchmark universities", () => {
    render(
      <ComparisonMatrix
        initialUniversityIds={["tum_cs", "oxford_cs", "rwth_engineering"]}
        isOpen={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText(/Universitetlərin Müqayisəsi & Xərc\/Viza Təhlili/i)).toBeInTheDocument();
    expect(screen.getByText(/İllik Təhsil Haqqı \(€\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Aylıq Yaşayış Xərci/i)).toBeInTheDocument();
    expect(screen.getByText(/Məzuniyyət İş Vizası \(PSWR\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Ekspert Müqayisə Qeydləri/i)).toBeInTheDocument();

    // Check universities
    expect(screen.getAllByText(/Technical University of Munich/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/University of Oxford/i).length).toBeGreaterThan(0);
  });

  it("allows removing a university from the comparison", () => {
    render(
      <ComparisonMatrix
        initialUniversityIds={["tum_cs", "oxford_cs", "rwth_engineering"]}
        isOpen={true}
        onClose={() => {}}
      />
    );

    const removeButtons = screen.getAllByTitle(/Müqayisədən çıxar/i);
    expect(removeButtons.length).toBe(3);

    fireEvent.click(removeButtons[0]);

    // Count should be 2 now
    expect(screen.getByText(/2 \/ 5/)).toBeInTheDocument();
  });
});
