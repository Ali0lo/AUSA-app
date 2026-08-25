import { ProgramRequirements } from "@/types";

export const DEMO_PROGRAMS: ProgramRequirements[] = [
  {
    program_id: 101,
    university_name: "Technical University of Munich (TU Munich)",
    program_name: "MSc Computer Science",
    degree_level: "master",
    field: "Computer Science",
    country: "Germany",
    min_gpa: 3.2,
    tuition_fee: 12000,
    currency: "EUR",
    min_ielts: 6.5,
    min_toefl: 88
  },
  {
    program_id: 102,
    university_name: "University College London (UCL)",
    program_name: "BSc Data Science",
    degree_level: "bachelor",
    field: "Data Science",
    country: "United Kingdom",
    min_gpa: 3.5,
    tuition_fee: 25000,
    currency: "GBP",
    min_ielts: 7,
    min_toefl: 100
  },
  {
    program_id: 103,
    university_name: "University of Amsterdam (UvA)",
    program_name: "MSc Artificial Intelligence",
    degree_level: "master",
    field: "Artificial Intelligence",
    country: "Netherlands",
    min_gpa: 3.3,
    tuition_fee: 15000,
    currency: "EUR",
    min_ielts: 6.5,
    min_toefl: 92
  }
];

export function findDemoPrograms(query: string): ProgramRequirements[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];

  return DEMO_PROGRAMS.filter((program) =>
    [
      program.program_name,
      program.university_name,
      program.field,
      program.country,
      program.degree_level
    ]
      .filter(Boolean)
      .some((value) => value?.toLowerCase().includes(normalized))
  );
}

export function getDemoProgram(programId: string | number | null): ProgramRequirements | undefined {
  if (programId === null) return undefined;
  return DEMO_PROGRAMS.find((program) => String(program.program_id) === String(programId));
}
