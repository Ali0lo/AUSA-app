import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI document advisor",
  description: "Ask questions against documents retrieved by the existing AUSA RAG endpoint."
};

export default function AdvisorLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
