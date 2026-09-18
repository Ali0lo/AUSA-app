import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SiteHeader } from "./SiteHeader";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() })
}));

vi.mock("next-auth/react", () => ({
  useSession: () => ({ data: null, status: "unauthenticated" }),
  signOut: vi.fn()
}));

describe("Visual Design System Specifications", () => {
  it("SiteHeader mounts with floating glassmorphism and primary CTA", () => {
    render(<SiteHeader />);
    const header = screen.getByRole("banner");
    expect(header).toBeInTheDocument();
    expect(header.className).toContain("backdrop-blur");
    expect(header.className).toContain("border-white/");

    // Check presence of create account button using button-primary
    const cta = screen.getByRole("link", { name: "Create account" });
    expect(cta).toBeInTheDocument();
    expect(cta.className).toContain("button-primary");
  });

  it("SiteHeader contains brand mark with gradient styling", () => {
    render(<SiteHeader />);
    const brandLink = screen.getByRole("link", { name: "AUSA home" });
    expect(brandLink).toBeInTheDocument();
    expect(brandLink.textContent).toContain("AUSA");
    expect(brandLink.textContent).toContain("University advisor");
  });
});
