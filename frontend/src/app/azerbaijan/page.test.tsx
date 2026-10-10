import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AzerbaijanPage from "@/app/azerbaijan/page";

const getAzerbaijanPredictions = vi.fn();
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    getAzerbaijanPredictions: (...args: unknown[]) => getAzerbaijanPredictions(...args)
  };
});

describe("AzerbaijanPage", () => {
  beforeEach(() => {
    getAzerbaijanPredictions.mockReset().mockResolvedValue({ items: [] });
  });

  it("fills the demo university, group and score, and loads that filter", async () => {
    const user = userEvent.setup();
    render(<AzerbaijanPage />);

    await user.click(screen.getByRole("button", { name: /Try demo example/i }));

    expect(screen.getByLabelText("University")).toHaveValue("unec");
    expect(screen.getByLabelText("DİM group")).toHaveValue("I qrup");
    expect(screen.getByLabelText("Your DİM score (optional)")).toHaveValue(610);
    await waitFor(() =>
      expect(getAzerbaijanPredictions).toHaveBeenLastCalledWith({ university: "unec", group: "I qrup" })
    );
  });
});
