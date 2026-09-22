import { describe, expect, it } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SopChecker } from "./SopChecker";

describe("SopChecker Component", () => {
  it("renders header controls and document type buttons", () => {
    render(<SopChecker />);
    expect(screen.getByText(/Sənəd Növünü Seçin/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Statement of Purpose \(SOP\)/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Academic CV \/ Resume/i })).toBeInTheDocument();
    expect(screen.getByText(/Hədəf Söz Sayı:/i)).toBeInTheDocument();
    expect(screen.getByText(/Dövlət Proqramı Müsabiqəsi Tələbləri/i)).toBeInTheDocument();
  });

  it("loads a pre-built exemplary SOP template via select dropdown", async () => {
    render(<SopChecker />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "data_science_state_programme" } });

    const textarea = screen.getByPlaceholderText(/Statement of Purpose və ya motivasiya məktubunuzu bura yapışdırın/i) as HTMLTextAreaElement;
    expect(textarea.value).toContain("Data Science");
    expect(textarea.value).toContain("Baku State University");
  });

  it("analyzes sample SOP text and displays rubric sections and grade gauge", async () => {
    render(<SopChecker />);
    
    // Default initial text is CS AI template
    expect(screen.getByText(/SOP Qiymətləndirmə Rubrikası/i)).toBeInTheDocument();
    expect(screen.getByText(/Zəruri Esse Hissələri/i)).toBeInTheDocument();
    expect(screen.getByText(/Uzunluq və Abzas Qaydası/i)).toBeInTheDocument();
    expect(screen.getByText(/Şablonsuz Orijinallıq/i)).toBeInTheDocument();
    expect(screen.getByText(/Zəruri Hissələrin Əhatəsi/i)).toBeInTheDocument();

    // Check mandatory narrative sections defined in analyzeSopLocal
    expect(screen.getByText(/İntellektual Giriş & Motivasiya/i)).toBeInTheDocument();
    expect(screen.getByText(/Akademik və Tədqiqat Bazası/i)).toBeInTheDocument();
    expect(screen.getByText(/Niyə Məhz Bu Universitet və Kafedra/i)).toBeInTheDocument();
    expect(screen.getByText(/Karyera Trayektoriyası və Məqsədlər/i)).toBeInTheDocument();
  });

  it("detects clichés when entered into the SOP text", async () => {
    render(<SopChecker />);
    const textarea = screen.getByPlaceholderText(/Statement of Purpose və ya motivasiya məktubunuzu bura yapışdırın/i);
    fireEvent.change(textarea, {
      target: {
        value: "Since childhood, I have always dreamed of becoming an engineer. I think outside the box and work hard to achieve my passionate goals."
      }
    });

    await waitFor(() => {
      // Cliché issues should be rendered in the feedback cards
      expect(screen.getByText(/Since childhood/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("switches to CV mode and displays CV analysis metrics", async () => {
    render(<SopChecker />);
    const cvTabBtn = screen.getByRole("button", { name: /Academic CV \/ Resume/i });
    fireEvent.click(cvTabBtn);

    expect(screen.getByText(/Academic CV Qiymətləndirməsi/i)).toBeInTheDocument();
    expect(screen.getByText(/CV Bənd və Metrika Analizi/i)).toBeInTheDocument();
    expect(screen.getByText(/Ümumi Bəndlər/i)).toBeInTheDocument();
    expect(screen.getByText(/Rəqəmlə Ölçülən/i)).toBeInTheDocument();
    expect(screen.getByText(/Aşkarlanmış Bölmələr:/i)).toBeInTheDocument();

    // Default sample CV has EDUCATION, EXPERIENCE, PROJECTS, SKILLS
    expect(screen.getByText(/✓ EDUCATION/i)).toBeInTheDocument();
    expect(screen.getByText(/✓ EXPERIENCE/i)).toBeInTheDocument();
  });

  it("clears content when clear button is clicked", () => {
    render(<SopChecker />);
    const textarea = screen.getByPlaceholderText(/Statement of Purpose və ya motivasiya məktubunuzu bura yapışdırın/i) as HTMLTextAreaElement;
    expect(textarea.value.length).toBeGreaterThan(0);

    const clearBtn = screen.getByRole("button", { name: /Təmizlə/i });
    fireEvent.click(clearBtn);

    expect(textarea.value).toBe("");
  });
});
