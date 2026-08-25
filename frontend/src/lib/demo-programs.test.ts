import { describe, expect, it } from "vitest";
import { DEMO_PROGRAMS, findDemoPrograms, getDemoProgram } from "@/lib/demo-programs";

describe("demo programme catalogue", () => {
  it("preserves the three original programme identifiers", () => {
    expect(DEMO_PROGRAMS.map((program) => program.program_id)).toEqual([101, 102, 103]);
  });

  it("searches programme, university, field, country, and degree", () => {
    expect(findDemoPrograms("UCL").map((program) => program.program_id)).toEqual([102]);
    expect(findDemoPrograms("Netherlands").map((program) => program.program_id)).toEqual([103]);
    expect(findDemoPrograms("master").map((program) => program.program_id)).toEqual([101, 103]);
    expect(findDemoPrograms("   ")).toEqual([]);
  });

  it("looks up numeric and string identifiers without inventing records", () => {
    expect(getDemoProgram("101")?.program_name).toBe("MSc Computer Science");
    expect(getDemoProgram(999)).toBeUndefined();
    expect(getDemoProgram(null)).toBeUndefined();
  });
});
