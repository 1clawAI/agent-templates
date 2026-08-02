/**
 * 1Claw Agent Memory adapter for ElizaOS.
 *
 * Implements the ElizaOS MemoryAdapter interface using the 1Claw sidecar API,
 * providing persistent memory for ElizaOS-based agents.
 *
 * @example
 * ```typescript
 * import { OneclawMemoryAdapter } from "./adapter";
 *
 * const memory = new OneclawMemoryAdapter({
 *   namespace: "eliza-agent",
 *   sidecarUrl: "http://localhost:8080",
 * });
 *
 * await memory.set("user-prefs", { theme: "dark" });
 * const prefs = await memory.get("user-prefs");
 * ```
 */

export interface MemoryEntry {
  key: string;
  value: unknown;
  tier: "scratch" | "durable" | "semantic";
  createdAt?: string;
  updatedAt?: string;
}

export interface SearchResult {
  key: string;
  value: unknown;
  score: number;
}

export interface OneclawMemoryConfig {
  namespace?: string;
  sidecarUrl?: string;
  tier?: "scratch" | "durable" | "semantic";
  ttlSeconds?: number;
}

export interface MemoryAdapter {
  get(key: string): Promise<unknown | null>;
  set(key: string, value: unknown): Promise<void>;
  delete(key: string): Promise<void>;
  list(): Promise<string[]>;
  search?(query: string, topK?: number): Promise<SearchResult[]>;
  clear(): Promise<void>;
}

export class OneclawMemoryAdapter implements MemoryAdapter {
  private readonly namespace: string;
  private readonly sidecarUrl: string;
  private readonly tier: "scratch" | "durable" | "semantic";
  private readonly ttlSeconds: number | undefined;

  constructor(config: OneclawMemoryConfig = {}) {
    this.namespace = config.namespace ?? "elizaos";
    this.sidecarUrl = config.sidecarUrl ?? "http://localhost:8080";
    this.tier = config.tier ?? "durable";
    this.ttlSeconds = config.ttlSeconds;
  }

  private url(key?: string): string {
    const base = `${this.sidecarUrl}/memory/${this.namespace}`;
    return key ? `${base}/${key}` : base;
  }

  async get(key: string): Promise<unknown | null> {
    const resp = await fetch(this.url(key) + `?tier=${this.tier}`);
    if (resp.status === 404) return null;
    if (!resp.ok) throw new Error(`Memory get failed: ${resp.status}`);
    const data = await resp.json();
    const value = data.value;
    if (typeof value === "string") {
      try {
        return JSON.parse(value);
      } catch {
        return value;
      }
    }
    return value;
  }

  async set(key: string, value: unknown): Promise<void> {
    const body: Record<string, unknown> = {
      value: typeof value === "string" ? value : JSON.stringify(value),
      tier: this.tier,
    };
    if (this.ttlSeconds !== undefined) {
      body.ttl_seconds = this.ttlSeconds;
    }

    const resp = await fetch(this.url(key), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error(`Memory set failed: ${resp.status}`);
  }

  async delete(key: string): Promise<void> {
    const resp = await fetch(this.url(key), { method: "DELETE" });
    if (!resp.ok && resp.status !== 404) {
      throw new Error(`Memory delete failed: ${resp.status}`);
    }
  }

  async list(): Promise<string[]> {
    const resp = await fetch(this.url());
    if (resp.status === 404) return [];
    if (!resp.ok) throw new Error(`Memory list failed: ${resp.status}`);
    const data = await resp.json();
    const entries: Array<{ key: string }> = data.entries ?? [];
    return entries.map((e) => e.key);
  }

  async search(query: string, topK = 5): Promise<SearchResult[]> {
    const resp = await fetch(`${this.sidecarUrl}/memory/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        namespace: this.namespace,
        query,
        top_k: topK,
      }),
    });
    if (resp.status === 404) return [];
    if (!resp.ok) throw new Error(`Memory search failed: ${resp.status}`);
    const data = await resp.json();
    return data.results ?? [];
  }

  async clear(): Promise<void> {
    const keys = await this.list();
    await Promise.all(keys.map((k) => this.delete(k)));
  }
}

export class OneclawScratchAdapter extends OneclawMemoryAdapter {
  constructor(config: Omit<OneclawMemoryConfig, "tier"> & { ttlSeconds?: number } = {}) {
    super({
      ...config,
      tier: "scratch",
      ttlSeconds: config.ttlSeconds ?? 3600,
    });
  }
}

export class OneclawSemanticAdapter extends OneclawMemoryAdapter {
  constructor(config: Omit<OneclawMemoryConfig, "tier"> = {}) {
    super({ ...config, tier: "semantic" });
  }
}
