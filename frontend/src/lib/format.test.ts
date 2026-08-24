import { describe, expect, it } from "vitest";
import { formatDocumentName, formatMoney, safeExternalUrl } from "@/lib/format";

describe("format helpers", () => {
  it("formats money and document identifiers", () => {
    expect(formatMoney(12000, "EUR")).toContain("12,000");
    expect(formatDocumentName("official_transcript")).toBe("Official Transcript");
  });

  it("allows only absolute HTTP source links", () => {
    expect(safeExternalUrl("https://university.example/rules")).toBe("https://university.example/rules");
    expect(safeExternalUrl("http://university.example/rules")).toBe("http://university.example/rules");
    expect(safeExternalUrl("javascript:alert(1)")).toBeUndefined();
    expect(safeExternalUrl("/relative-source")).toBeUndefined();
  });
});
