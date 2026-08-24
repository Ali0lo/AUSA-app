import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatBox } from "@/components/ChatBox";

const api = vi.hoisted(() => ({
  sendChatMessage: vi.fn(),
  getUserFacingError: vi.fn(() => ({ title: "Backend unavailable", message: "The API is offline." }))
}));

vi.mock("@/lib/api", () => api);

describe("ChatBox", () => {
  beforeEach(() => {
    api.sendChatMessage.mockReset();
    api.getUserFacingError.mockClear();
  });

  it("renders returned evidence and blocks unsafe source links", async () => {
    const user = userEvent.setup();
    api.sendChatMessage.mockResolvedValue({
      reply: "The backend answer.",
      sources: [{ content_snippet: "Evidence text", source_url: "javascript:alert(1)", page: 12 }]
    });
    render(<ChatBox lockedMode="rag" />);

    await user.type(screen.getByRole("textbox", { name: "Question" }), "What is required?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("The backend answer.")).toBeInTheDocument();
    expect(screen.getByText("Page 12")).toBeInTheDocument();
    expect(screen.getByText("The returned source URL is not a safe web address.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open source" })).not.toBeInTheDocument();
  });

  it("shows a retry action without duplicating the failed user message", async () => {
    const user = userEvent.setup();
    api.sendChatMessage
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ reply: "Recovered answer.", sources: [] });
    render(<ChatBox lockedMode="rag" />);

    await user.type(screen.getByRole("textbox", { name: "Question" }), "Retry this question");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Backend unavailable");

    await user.click(screen.getByRole("button", { name: "Retry message" }));
    expect(await screen.findByText("Recovered answer.")).toBeInTheDocument();
    expect(screen.getAllByText("Retry this question")).toHaveLength(1);
    expect(api.sendChatMessage).toHaveBeenCalledTimes(2);
  });
});
