import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SiteHeader } from "@/components/SiteHeader";

const navMock = vi.hoisted(() => ({
  pathname: "/plan",
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.pathname,
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, onClick, ...rest }: any) => (
    <a
      href={href}
      onClick={(e) => {
        e.preventDefault();
        onClick?.(e);
      }}
      {...rest}
    >
      {children}
    </a>
  ),
}));

vi.mock("next-auth/react", () => ({
  useSession: () => ({ data: null, status: "unauthenticated" }),
  signOut: vi.fn(),
}));

describe("SiteHeader Component", () => {
  beforeEach(() => {
    navMock.pathname = "/plan";
  });

  it("renders brand logo linking to home", () => {
    render(<SiteHeader />);
    const brandLink = screen.getByRole("link", { name: /AUSA home/i });
    expect(brandLink).toBeInTheDocument();
    expect(brandLink).toHaveAttribute("href", "/");
  });

  it("renders all primary navigation links on desktop", () => {
    render(<SiteHeader />);
    const primaryNav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(primaryNav).toBeInTheDocument();

    expect(screen.getByRole("link", { name: "Plan my route" })).toHaveAttribute("href", "/plan");
    expect(screen.getByRole("link", { name: "Target University" })).toHaveAttribute("href", "/target");
    expect(screen.getByRole("link", { name: "Tətbiq Paneli" })).toHaveAttribute("href", "/dashboard");
    expect(screen.getByRole("link", { name: "Finances & Visa" })).toHaveAttribute("href", "/finance");
    expect(screen.getByRole("link", { name: "Scholarships" })).toHaveAttribute("href", "/scholarships");
    expect(screen.getByRole("link", { name: "DİM Kalkulyator" })).toHaveAttribute("href", "/dim-calculator");
    expect(screen.getByRole("link", { name: "SOP & CV Yoxlayıcı" })).toHaveAttribute("href", "/sop-checker");
    expect(screen.getByRole("link", { name: "Qəbul Təqvimi" })).toHaveAttribute("href", "/timeline");
  });

  it("highlights the active route based on current pathname", () => {
    navMock.pathname = "/dashboard";
    render(<SiteHeader />);

    const dashboardLink = screen.getByRole("link", { name: "Tətbiq Paneli" });
    expect(dashboardLink).toHaveAttribute("aria-current", "page");
    expect(dashboardLink.className).toContain("text-white font-semibold");

    const planLink = screen.getByRole("link", { name: "Plan my route" });
    expect(planLink).not.toHaveAttribute("aria-current");
  });

  it("highlights sub-paths matching parent route", () => {
    navMock.pathname = "/finance/simulator";
    render(<SiteHeader />);

    const financeLink = screen.getByRole("link", { name: "Finances & Visa" });
    expect(financeLink).toHaveAttribute("aria-current", "page");
  });

  it("toggles mobile navigation open and closed on menu button click", async () => {
    const user = userEvent.setup();
    render(<SiteHeader />);

    const toggleBtn = screen.getByRole("button", { name: "Open navigation" });
    expect(toggleBtn).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("navigation", { name: "Mobile navigation" })).not.toBeInTheDocument();

    // Open mobile menu
    await user.click(toggleBtn);
    expect(screen.getByRole("button", { name: "Close navigation" })).toHaveAttribute("aria-expanded", "true");
    const mobileNav = screen.getByRole("navigation", { name: "Mobile navigation" });
    expect(mobileNav).toBeInTheDocument();

    // Close mobile menu
    await user.click(screen.getByRole("button", { name: "Close navigation" }));
    expect(screen.queryByRole("navigation", { name: "Mobile navigation" })).not.toBeInTheDocument();
  });

  it("closes mobile menu when clicking a navigation link inside mobile drawer", async () => {
    const user = userEvent.setup();
    render(<SiteHeader />);

    // Open mobile menu
    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    const mobileNav = screen.getByRole("navigation", { name: "Mobile navigation" });
    expect(mobileNav).toBeInTheDocument();

    // Click link inside mobile nav
    const mobileLinks = screen.getAllByRole("link", { name: "Tətbiq Paneli" });
    const mobileDashboardLink = mobileLinks[mobileLinks.length - 1];
    await user.click(mobileDashboardLink);

    // Menu should close
    expect(screen.queryByRole("navigation", { name: "Mobile navigation" })).not.toBeInTheDocument();
  });
});
