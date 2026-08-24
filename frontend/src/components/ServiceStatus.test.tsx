import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ServiceStatus } from "@/components/ServiceStatus";

describe("ServiceStatus", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reports a healthy backend and supports a manual recheck", async () => {
    const user = userEvent.setup();
    const response = () => new Response(JSON.stringify({ status: "healthy", service: "AUSA", version: "0.1.0", environment: "test" }));
    fetchMock.mockImplementation(async () => response());
    render(<ServiceStatus />);

    expect(await screen.findByText("Backend online · v0.1.0")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Backend online · v0.1.0")).toBeInTheDocument();
  });

  it("names an offline backend", async () => {
    fetchMock.mockRejectedValue(new TypeError("fetch failed"));
    render(<ServiceStatus />);
    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });
});
