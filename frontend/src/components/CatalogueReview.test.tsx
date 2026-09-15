import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { CatalogueReview } from "./CatalogueReview";
import { catalogueRow } from "@/test/catalogue";
import { fetchCatalogueReview, verifyCatalogueRow, ApiError } from "@/lib/api";
vi.mock("@/lib/api", async () => ({ ...(await vi.importActual<typeof import("@/lib/api")>("@/lib/api")), fetchCatalogueReview: vi.fn(), verifyCatalogueRow: vi.fn() }));
const revision = "a".repeat(64);
beforeEach(() => { vi.mocked(fetchCatalogueReview).mockReset().mockResolvedValue([{revision, requirement: catalogueRow()}]); vi.mocked(verifyCatalogueRow).mockReset().mockResolvedValue(undefined); });
it("requires explicit acknowledgement and sends the displayed revision with authentication", async () => {
  render(<CatalogueReview token="test-token" />);
  const button = await screen.findByRole("button", {name: "Verify this catalogue row"});
  expect(button).toBeDisabled();
  await userEvent.click(screen.getByRole("checkbox"));
  await userEvent.click(button);
  expect(verifyCatalogueRow).toHaveBeenCalledWith(1, revision, "test-token");
  expect(await screen.findByText(/No pending catalogue rows/)).toBeInTheDocument();
});
it("retains the row and explains a stale review conflict", async () => {
  vi.mocked(verifyCatalogueRow).mockRejectedValueOnce(new ApiError("The requirements changed. Reload and review.", "http", 409));
  render(<CatalogueReview token="test-token" />);
  await userEvent.click(await screen.findByRole("checkbox"));
  await userEvent.click(screen.getByRole("button", {name: "Verify this catalogue row"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("requirements changed");
  expect(screen.getByRole("heading", {name: /Test University/})).toBeInTheDocument();
});
it("cannot approve a row without scoped evidence", async () => {
  vi.mocked(fetchCatalogueReview).mockResolvedValueOnce([{revision, requirement: catalogueRow({evidence: []})}]);
  render(<CatalogueReview token="test-token" />);
  expect(await screen.findByRole("checkbox")).toBeDisabled();
  expect(screen.getByRole("button", {name: "Verify this catalogue row"})).toBeDisabled();
});
