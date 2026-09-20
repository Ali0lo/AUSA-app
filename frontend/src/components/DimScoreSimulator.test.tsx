import { describe, expect, it } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DimScoreSimulator } from "./DimScoreSimulator";

describe("DimScoreSimulator Component", () => {
  it("renders group selector and default Qrup I subjects", () => {
    render(<DimScoreSimulator />);
    expect(screen.getByText(/İxtisas Qrupunu Seçin/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^I İxtisas Qrupu$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^II İxtisas Qrupu$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^III İxtisas Qrupu$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^IV İxtisas Qrupu$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^V İxtisas Qrupu$/ })).toBeInTheDocument();

    // Default Group 1 subjects
    expect(screen.getByText(/Buraxılış İmtahanı \(Attestat\)/i)).toBeInTheDocument();
    expect(screen.getByText(/İxtisas Bloku İmtahanı/i)).toBeInTheDocument();
    expect(screen.getAllByText(/İnformatika/i).length).toBeGreaterThan(0);
  });

  it("switches to Group 2 and renders geography subject", () => {
    render(<DimScoreSimulator />);
    const g2Button = screen.getByRole("button", { name: /^II İxtisas Qrupu$/ });
    fireEvent.click(g2Button);

    expect(screen.getByText(/Coğrafiya/i)).toBeInTheDocument();
    expect(screen.getByText(/İqtisadiyyat, idarəetmə, maliyyə/i)).toBeInTheDocument();
  });

  it("switches between detailed question mode and direct score mode", () => {
    render(<DimScoreSimulator />);
    const directModeBtn = screen.getByRole("button", { name: /Dəqiq Bal ilə/i });
    fireEvent.click(directModeBtn);

    expect(screen.getByText(/Dəqiq İmtahan Ballarınız/i)).toBeInTheDocument();
    expect(screen.getByText(/Buraxılış İmtahanı Balı \(Maks\. 300\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Blok İmtahanı Balı \(Maks\. 400\)/i)).toBeInTheDocument();

    const detailedModeBtn = screen.getByRole("button", { name: /Sual Sayı ilə/i });
    fireEvent.click(detailedModeBtn);
    expect(screen.getByText(/Buraxılış İmtahanı \(Attestat\)/i)).toBeInTheDocument();
  });

  it("displays BHOS 650+ benchmark clearance when score is high", () => {
    render(<DimScoreSimulator />);
    const directModeBtn = screen.getByRole("button", { name: /Dəqiq Bal ilə/i });
    fireEvent.click(directModeBtn);

    // Initial direct values: 240 + 320 = 560
    expect(screen.getByText(/560/i)).toBeInTheDocument();

    // Adjust direct inputs to exceed 650
    const sliders = screen.getAllByRole("slider");
    fireEvent.change(sliders[0], { target: { value: "280" } }); // Buraxilis: 280
    fireEvent.change(sliders[1], { target: { value: "380" } }); // Blok: 380

    // Total: 660 -> Clears BANM 650+ benchmark
    expect(screen.getByText(/660/i)).toBeInTheDocument();
    expect(screen.getByText(/BANM \(BHOS\) 650\+ Həddini Keçir!/i)).toBeInTheDocument();
  });

  it("filters recommendations by university chip", async () => {
    render(<DimScoreSimulator />);
    const adaChip = screen.getByRole("button", { name: "ADA" });
    fireEvent.click(adaChip);

    await waitFor(() => {
      const adaMatches = screen.getAllByText(/ADA/i);
      expect(adaMatches.length).toBeGreaterThan(0);
    });
  });

  it("filters recommendations by chance level", async () => {
    render(<DimScoreSimulator />);
    const safeChip = screen.getByRole("button", { name: /Yüksək Şans \(Safe\) 🟢/i });
    fireEvent.click(safeChip);

    await waitFor(() => {
      const safePills = screen.getAllByText(/Yüksək Şans/i);
      expect(safePills.length).toBeGreaterThan(0);
    });
  });

  it("filters specialties by search input query", async () => {
    render(<DimScoreSimulator />);
    const searchInput = screen.getByPlaceholderText(/İxtisas və ya universitet axtar/i);
    fireEvent.change(searchInput, { target: { value: "Kompüter" } });

    await waitFor(() => {
      const csRows = screen.getAllByText(/Kompüter/i);
      expect(csRows.length).toBeGreaterThan(0);
    });
  });
});
