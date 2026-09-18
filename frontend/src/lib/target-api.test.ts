import { afterEach, describe, expect, it, vi } from "vitest";
import { assessTargetGap, fetchTargetCatalog } from "./api";
import type { TargetCatalogItem, TargetGapResponse } from "@/types";

afterEach(() => vi.unstubAllGlobals());

const mockCatalogItem: TargetCatalogItem = {
  university_name: "Technical University of Munich",
  program_name: "Informatics B.Sc.",
  level: "bachelor",
  country_code: "DE",
  source_type: "curated",
  source_url: "https://www.tum.de"
};

const mockGapResponse: TargetGapResponse = {
  found: true,
  university_name: "Technical University of Munich",
  program_name: "Informatics B.Sc.",
  level: "bachelor",
  country_code: "DE",
  route_status: "UNLOCKABLE",
  route_gap_statement: "Azerbaijani 11-year Attestat requires a Studienkolleg prep course or 1 year of university before direct entry.",
  unlock_steps: ["Complete Studienkolleg (T-Kurs) or 1 year accredited university in Azerbaijan"],
  unlock_time_months: 12,
  unlock_cost_azn_low: 15000,
  unlock_cost_azn_high: 25000,
  checklist: [
    {
      name: "Qualification Recognition",
      requirement: "12 years equivalent or Studienkolleg",
      student_value: "attestat",
      status: "GAP",
      explanation: "Direct bachelor entry requires Studienkolleg"
    }
  ],
  application_portal: "TUMonline",
  application_deadline: "July 15",
  application_fee: 0,
  currency: "EUR",
  documents_required: "Attestat, German B2/C1, VPD via uni-assist",
  alternatives: [
    {
      university_name: "RWTH Aachen University",
      country_code: "DE",
      reason: "Alternative German technical university with similar profile"
    }
  ],
  provenance: "human-verified",
  source_url: "https://www.tum.de/en/studies/degree-programs/detail/informatics-bachelor-of-science-bsc",
  last_checked: "2026-09-01",
  notes: "Uni-assist VPD required"
};

describe("target API client functions", () => {
  it("fetches target catalog with filters and parses successfully", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([mockCatalogItem]), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const items = await fetchTargetCatalog({ level: "bachelor", country: "DE" });
    expect(items).toHaveLength(1);
    expect(items[0].university_name).toBe("Technical University of Munich");
    expect(fetchMock.mock.calls[0][0]).toContain("/routes/catalog?level=bachelor&country=DE");
  });

  it("throws invalid-response when target catalog item is malformed", async () => {
    const malformed = [{ university_name: "Technical University of Munich" }]; // missing required keys
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(malformed), { status: 200 })));

    await expect(fetchTargetCatalog()).rejects.toThrow(/did not match the documented API contract/);
  });

  it("assesses target gap and parses complete response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(mockGapResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const res = await assessTargetGap({
      university_name: "Technical University of Munich",
      level: "bachelor",
      qualification_held: "attestat"
    });

    expect(res.found).toBe(true);
    expect(res.route_status).toBe("UNLOCKABLE");
    expect(res.checklist).toHaveLength(1);
    expect(res.checklist[0].status).toBe("GAP");
    expect(fetchMock).toHaveBeenCalled();
  });

  it("rejects target gap evaluation when checklist is invalid", async () => {
    const invalid = { ...mockGapResponse, checklist: "not-an-array" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(invalid), { status: 200 })));

    await expect(
      assessTargetGap({ university_name: "Technical University of Munich" })
    ).rejects.toThrow(/did not match the documented API contract/);
  });
});
