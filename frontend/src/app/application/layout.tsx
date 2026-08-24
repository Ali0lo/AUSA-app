import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Application assistant",
  description: "Use the current AUSA application-agent demonstration and local document checklist."
};

export default function ApplicationLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
