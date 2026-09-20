import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FinanceSimulator } from "./FinanceSimulator";

describe("FinanceSimulator Component", () => {
  beforeEach(() => {
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });
  });

  it("renders page title and statutory proof-of-funds badge", () => {
    render(<FinanceSimulator />);
    expect(screen.getByText(/Student Visa, Blocked Account & Living Cost Simulator/i)).toBeInTheDocument();
    expect(screen.getByText(/Statutory Visa & Funds Simulator/i)).toBeInTheDocument();
  });

  it("renders all 6 navigation tabs", () => {
    render(<FinanceSimulator />);
    expect(screen.getByRole("button", { name: /Germany Sperrkonto/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /UK CAS Maintenance/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /US Form I-20/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Italy ISEE-U/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Compare 4 Countries/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Currency Converter/i })).toBeInTheDocument();
  });

  it("displays Germany Sperrkonto statutory calculations by default", () => {
    render(<FinanceSimulator />);
    // German blocked account base €11,904 + €89 + €100 = €12,093
    expect(screen.getByText(/€12,093/i)).toBeInTheDocument();
    expect(screen.getByText(/Statutory Auswärtiges Amt Rule/i)).toBeInTheDocument();
    expect(screen.getByText(/€992\/month/i)).toBeInTheDocument();
  });

  it("switches to UK tab and displays 28-day bank statement requirement", () => {
    render(<FinanceSimulator />);
    const ukTab = screen.getByRole("button", { name: /UK CAS Maintenance/i });
    fireEvent.click(ukTab);

    expect(screen.getByText(/UKVI Appendix Student Parameters/i)).toBeInTheDocument();
    expect(screen.getByText(/Strict 28-Day Bank Statement Rule/i)).toBeInTheDocument();
    expect(screen.getByText(/Strict 28-Day Bank Statement Requirement/i)).toBeInTheDocument();
  });

  it("switches to US tab and displays Form I-20 Cost of Attendance", () => {
    render(<FinanceSimulator />);
    const usTab = screen.getByRole("button", { name: /US Form I-20/i });
    fireEvent.click(usTab);

    expect(screen.getByText(/US Form I-20 & F-1 Parameters/i)).toBeInTheDocument();
    expect(screen.getByText(/Official Form I-20 Minimum Liquidity Required/i)).toBeInTheDocument();
    expect(screen.getByText(/SEVIS I-901 Fee/i)).toBeInTheDocument();
    expect(screen.getByText(/\$350/i)).toBeInTheDocument();
  });

  it("switches to Italy tab and displays ISEE-U DSU assessment", () => {
    render(<FinanceSimulator />);
    const itTab = screen.getByRole("button", { name: /Italy ISEE-U/i });
    fireEvent.click(itTab);

    expect(screen.getByText(/Italy ISEE-U \/ DSU Grant Parameters/i)).toBeInTheDocument();
    expect(screen.getByText(/DSU SCHOLARSHIP ELIGIBLE/i)).toBeInTheDocument();
    expect(screen.getByText(/Regional Cash Stipend/i)).toBeInTheDocument();
  });

  it("switches to Compare tab and renders 4-country benchmark cards", () => {
    render(<FinanceSimulator />);
    const compareTab = screen.getByRole("button", { name: /Compare 4 Countries/i });
    fireEvent.click(compareTab);

    expect(screen.getByText(/Your Disposable First-Year Budget \(AZN\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Germany/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/United Kingdom/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/United States/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Italy/i).length).toBeGreaterThanOrEqual(1);
  });

  it("switches to Currency Converter tab and renders multi-currency breakdown", () => {
    render(<FinanceSimulator />);
    const convTab = screen.getByRole("button", { name: /Currency Converter/i });
    fireEvent.click(convTab);

    expect(screen.getByText(/Real-Time CBAR Currency Converter/i)).toBeInTheDocument();
    expect(screen.getByText(/Converted Output/i)).toBeInTheDocument();
    expect(screen.getByText(/Official CBAR Fixed Rate Matrix/i)).toBeInTheDocument();
  });

  it("copies summary to clipboard when copy button is clicked", async () => {
    render(<FinanceSimulator />);
    const copyBtn = screen.getByRole("button", { name: /Copy summary/i });
    fireEvent.click(copyBtn);

    expect(navigator.clipboard.writeText).toHaveBeenCalled();
    expect(screen.getByText(/Copied to clipboard/i)).toBeInTheDocument();
  });
});
