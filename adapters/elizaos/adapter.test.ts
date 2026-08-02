import { describe, it, expect, beforeEach, vi } from "vitest";
import { OneclawMemoryAdapter, OneclawScratchAdapter, OneclawSemanticAdapter } from "./adapter";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  };
}

describe("OneclawMemoryAdapter", () => {
  let memory: OneclawMemoryAdapter;

  beforeEach(() => {
    vi.clearAllMocks();
    memory = new OneclawMemoryAdapter({
      namespace: "test",
      sidecarUrl: "http://localhost:9999",
    });
  });

  it("get returns value when found", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ value: '{"x":1}' }));
    const result = await memory.get("key1");
    expect(result).toEqual({ x: 1 });
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:9999/memory/test/key1?tier=durable"
    );
  });

  it("get returns null on 404", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(null, 404));
    const result = await memory.get("missing");
    expect(result).toBeNull();
  });

  it("set sends PUT with correct body", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(null));
    await memory.set("key1", { hello: "world" });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:9999/memory/test/key1",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ value: '{"hello":"world"}', tier: "durable" }),
      })
    );
  });

  it("delete sends DELETE", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(null));
    await memory.delete("key1");
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:9999/memory/test/key1",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("list returns keys", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ entries: [{ key: "a" }, { key: "b" }] })
    );
    const keys = await memory.list();
    expect(keys).toEqual(["a", "b"]);
  });

  it("search posts query", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ results: [{ key: "r1", value: "v", score: 0.9 }] })
    );
    const results = await memory.search("test query", 3);
    expect(results).toHaveLength(1);
    expect(results[0].score).toBe(0.9);
  });
});

describe("OneclawScratchAdapter", () => {
  it("uses scratch tier with TTL", async () => {
    const scratch = new OneclawScratchAdapter({
      namespace: "tmp",
      sidecarUrl: "http://localhost:9999",
      ttlSeconds: 600,
    });
    mockFetch.mockResolvedValueOnce(jsonResponse(null));
    await scratch.set("k", "v");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.tier).toBe("scratch");
    expect(body.ttl_seconds).toBe(600);
  });
});

describe("OneclawSemanticAdapter", () => {
  it("uses semantic tier", async () => {
    const semantic = new OneclawSemanticAdapter({
      namespace: "kb",
      sidecarUrl: "http://localhost:9999",
    });
    mockFetch.mockResolvedValueOnce(jsonResponse(null));
    await semantic.set("k", "v");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.tier).toBe("semantic");
  });
});
