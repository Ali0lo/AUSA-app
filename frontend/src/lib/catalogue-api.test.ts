import { afterEach, expect, it, vi } from "vitest";
import { fetchCatalogue, fetchCatalogueReview } from "./api";
import { catalogueRow } from "@/test/catalogue";
afterEach(() => vi.unstubAllGlobals());
it("loads catalogue pages until the reported total is covered", async () => {
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({status:"listed",total:2,items:[catalogueRow()]})))
    .mockResolvedValueOnce(new Response(JSON.stringify({status:"listed",total:2,items:[catalogueRow({id:2})]})));
  vi.stubGlobal("fetch", fetch);
  expect((await fetchCatalogue("master")).items).toHaveLength(2);
  expect(fetch.mock.calls[1][0]).toContain("offset=1");
});
it("rejects malformed evidence before a component can dereference it", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({status:"listed",total:1,items:[{...catalogueRow(),evidence:[{url:"https://example.edu",fields:null}]}]}))));
  await expect(fetchCatalogue("master")).rejects.toThrow();
});
it("rejects a review without an id", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([{revision:"a".repeat(64),requirement:catalogueRow({id:undefined})}]))));
  await expect(fetchCatalogueReview("master","token")).rejects.toThrow();
});
