import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DocumentChecklist } from "@/components/DocumentChecklist";

describe("DocumentChecklist", () => {
  it("shows every state and makes each local action observable", async () => {
    const user = userEvent.setup();
    const toggle = vi.fn();
    render(<DocumentChecklist missingDocuments={["official_transcript"]} onToggleDocument={toggle} />);

    expect(screen.getByText("1 missing")).toBeInTheDocument();
    expect(screen.getByText("Official Transcript")).toBeInTheDocument();
    expect(screen.getAllByText("Marked ready")).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: "Mark ready" }));
    expect(toggle).toHaveBeenCalledWith("official_transcript");
  });
});
