import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NavAuthButton } from "@/components/NavAuthButton";

const auth = vi.hoisted(() => ({ useSession: vi.fn(), signOut: vi.fn() }));
const navigation = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("next-auth/react", () => auth);
vi.mock("next/navigation", () => ({ useRouter: () => navigation }));

describe("NavAuthButton", () => {
  beforeEach(() => {
    auth.useSession.mockReset();
    auth.signOut.mockReset();
    navigation.push.mockReset();
    navigation.refresh.mockReset();
  });

  it("provides working account routes to a guest", () => {
    auth.useSession.mockReturnValue({ data: null, status: "unauthenticated" });
    render(<NavAuthButton />);

    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/sign-in");
    expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute("href", "/register");
  });

  it("ends an authenticated session and returns home", async () => {
    const user = userEvent.setup();
    auth.useSession.mockReturnValue({ data: { user: { email: "student@example.com" } }, status: "authenticated" });
    auth.signOut.mockResolvedValue({ url: "http://localhost/" });
    render(<NavAuthButton />);

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(auth.signOut).toHaveBeenCalledWith({ callbackUrl: "/", redirect: false });
    expect(navigation.push).toHaveBeenCalledWith("/");
    expect(navigation.refresh).toHaveBeenCalledOnce();
  });

  it("reports a failed sign-out and preserves the active state", async () => {
    const user = userEvent.setup();
    auth.useSession.mockReturnValue({ data: { user: { email: "student@example.com" } }, status: "authenticated" });
    auth.signOut.mockRejectedValue(new Error("session endpoint failed"));
    render(<NavAuthButton />);

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Sign-out failed. The current session remains active.");
    expect(screen.getByRole("button", { name: "Sign out" })).toBeEnabled();
    expect(navigation.push).not.toHaveBeenCalled();
  });
});
