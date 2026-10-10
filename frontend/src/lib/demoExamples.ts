// Inputs for the live demo, behind the "Try demo example" buttons. Each was run against the
// full stack on 2026-10-10; docs/DEMO.md lists the result each one should produce.

export const DEMO_SENTENCE =
  "Attestatım var, DİM balım 610, IELTS 6.5, ildə 8000 manat büdcəm var, kompüter elmləri oxumaq istəyirəm, bakalavr.";

export const DEMO_TARGET = {
  university: "LMU Munich",
  ielts: "6.5",
  dimScore: "610"
} as const;

export const DEMO_AZERBAIJAN = {
  university: "unec",
  group: "I qrup",
  score: "610"
} as const;

export const DEMO_ADVISOR_QUESTIONS = [
  "Attestatla Münhen Texniki Universitetinə (TUM) bakalavra qəbul olmaq olar?",
  "What does Türkiye Bursları cover and what is the age limit?",
  "Which German universities does the State Programme fund for master's study?",
  "Can you recommend a good pizza place in Baku?"
] as const;

export const DEMO_AGENT_MESSAGE =
  "I finished school in Azerbaijan with an attestat, DIM score 610, IELTS 6.5, budget 8000 AZN per year. I want a bachelor's in Germany. What are my routes?";
