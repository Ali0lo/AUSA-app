import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LandingSearch } from "@/components/LandingSearch";

const navigation = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => navigation
}));

describe("LandingSearch", () => {
  beforeEach(() => navigation.push.mockReset());

  it("explains an empty search instead of doing nothing", async () => {
    const user = userEvent.setup();
    render(<LandingSearch />);

    await user.click(screen.getByRole("button", { name: "Search demo" }));

    expect(screen.getByRole("status")).toHaveTextContent("Enter a programme, university, field, or country");
    expect(navigation.push).not.toHaveBeenCalled();
  });

  it("opens matching when exactly one programme matches", async () => {
    const user = userEvent.setup();
    render(<LandingSearch />);

    await user.type(screen.getByRole("combobox", { name: "Search the demo programme catalogue" }), "UCL");
    await user.click(screen.getByRole("button", { name: "Search demo" }));

    expect(navigation.push).toHaveBeenCalledWith("/match?program=102");
  });

  it("returns usable links for several matches and names an unavailable catalogue result", async () => {
    const user = userEvent.setup();
    render(<LandingSearch />);
    const input = screen.getByRole("combobox", { name: "Search the demo programme catalogue" });

    await user.type(input, "master");
    await user.click(screen.getByRole("button", { name: "Search demo" }));

    expect(screen.getByRole("status")).toHaveTextContent("2 demo programmes");
    expect(screen.getByRole("link", { name: "MSc Computer Science" })).toHaveAttribute("href", "/match?program=101");

    await user.clear(input);
    await user.type(input, "nonexistent course");
    await user.click(screen.getByRole("button", { name: "Search demo" }));

    expect(screen.getByRole("status")).toHaveTextContent("full catalogue is not implemented");
  });
});
