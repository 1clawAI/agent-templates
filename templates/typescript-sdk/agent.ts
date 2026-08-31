/**
 * Plain TypeScript agent using @1claw/sdk for vault access and signing,
 * with Vercel AI SDK for LLM interaction through Shroud.
 *
 * LLM calls route through the host daemon's /proxy when ONECLAW_SHROUD_SECRET
 * is set (spawn/init cloud mode). The container never sees agent or provider keys.
 */

import { request as httpRequest } from "node:http";
import { createServer } from "node:http";
import { OneclawClient } from "@1claw/sdk";
import { createOpenAI } from "@ai-sdk/openai";
import { generateText, tool } from "ai";
import { z } from "zod";

const SHROUD_URL = process.env.ONECLAW_SHROUD_URL ?? "https://shroud.1claw.co";
const LLM_VIA_SHROUD = process.env.ONECLAW_LLM_VIA_SHROUD === "true";
const MODEL = process.env.ONECLAW_SHROUD_MODEL ?? "gpt-4o-mini";
const PORT = parseInt(process.env.AGENT_INTERNAL_PORT ?? "3001", 10);
const DAEMON_SOCKET = process.env.ONECLAW_DAEMON_SOCKET ?? "/run/1claw/daemon.sock";
const SECRET_PREFIX = process.env.ONECLAW_SECRET_PREFIX ?? "";
const SHROUD_SECRET = process.env.ONECLAW_SHROUD_SECRET ?? "";
const SHROUD_API_KEY_SECRET = process.env.ONECLAW_SHROUD_API_KEY_SECRET ?? "";
const SHROUD_PROVIDER = process.env.ONECLAW_SHROUD_PROVIDER ?? "openai";

const conversationHistory: { role: "user" | "assistant"; content: string }[] = [];

const claw = new OneclawClient({
  apiKey: process.env.ONECLAW_AGENT_API_KEY,
  agentId: process.env.ONECLAW_AGENT_ID,
  baseUrl: process.env.ONECLAW_BASE_URL ?? "https://api.1claw.co",
});

function daemonRequest(
  method: string,
  path: string,
  body?: unknown,
): Promise<{ status: number; body: Record<string, unknown> | null }> {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : undefined;
    const req = httpRequest(
      {
        socketPath: DAEMON_SOCKET,
        path,
        method,
        headers: {
          "Content-Type": "application/json",
          ...(SECRET_PREFIX ? { "X-Secret-Prefix": SECRET_PREFIX } : {}),
          ...(payload ? { "Content-Length": Buffer.byteLength(payload) } : {}),
        },
        timeout: 120_000,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c) => chunks.push(c as Buffer));
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf-8");
          let parsed: Record<string, unknown> | null = null;
          try {
            parsed = text ? (JSON.parse(text) as Record<string, unknown>) : null;
          } catch {
            parsed = { raw: text };
          }
          resolve({ status: res.statusCode ?? 0, body: parsed });
        });
      },
    );
    req.on("error", reject);
    req.on("timeout", () => req.destroy(new Error("daemon request timed out")));
    if (payload) req.write(payload);
    req.end();
  });
}

/** Route outbound LLM HTTP through the host daemon (injects X-Shroud-Agent-Key). */
async function proxyViaDaemon(url: string, init?: RequestInit): Promise<Response> {
  if (!SHROUD_SECRET) {
    throw new Error(
      "Shroud is enabled but ONECLAW_SHROUD_SECRET is missing. Re-run spawn with --agent-key ocv_... so the daemon can inject credentials.",
    );
  }

  const headers: Record<string, string> = {};
  if (init?.headers) {
    const h = init.headers;
    if (h instanceof Headers) {
      h.forEach((v, k) => {
        headers[k] = v;
      });
    } else if (Array.isArray(h)) {
      for (const [k, v] of h) headers[k] = v;
    } else {
      Object.assign(headers, h as Record<string, string>);
    }
  }
  delete headers.authorization;
  delete headers.Authorization;
  headers["X-Shroud-Provider"] = headers["X-Shroud-Provider"] ?? SHROUD_PROVIDER;

  let body: string | undefined;
  if (typeof init?.body === "string") {
    body = init.body;
  } else if (init?.body != null) {
    body = String(init.body);
  }

  const proxyBody: Record<string, unknown> = {
    secretName: SHROUD_SECRET,
    url,
    method: init?.method ?? "GET",
    headers,
    body,
  };
  if (SHROUD_API_KEY_SECRET) {
    proxyBody.injectSecrets = [SHROUD_API_KEY_SECRET];
  }

  const r = await daemonRequest("POST", "/proxy", proxyBody);
  if (r.status !== 200) {
    const detail =
      (r.body && (r.body.error as string)) ||
      (r.body ? JSON.stringify(r.body) : "unknown daemon error");
    throw new Error(`Daemon proxy failed (${r.status}): ${detail}`);
  }

  const upstreamStatus = (r.body?.status as number) ?? 502;
  const upstreamBody =
    typeof r.body?.body === "string"
      ? r.body.body
      : JSON.stringify(r.body?.body ?? {});

  let errorMessage: string | undefined;
  if (upstreamStatus >= 400) {
    try {
      const parsed = JSON.parse(upstreamBody) as {
        error?: string | { message?: string };
        message?: string;
      };
      if (typeof parsed.error === "string") {
        errorMessage = parsed.error;
      } else if (parsed.error && typeof parsed.error.message === "string") {
        errorMessage = parsed.error.message;
      } else if (typeof parsed.message === "string") {
        errorMessage = parsed.message;
      }
    } catch {
      errorMessage = upstreamBody.slice(0, 400);
    }
  }

  if (errorMessage) {
    throw new Error(errorMessage);
  }

  const responseHeaders = (r.body?.headers as Record<string, string>) ?? {
    "Content-Type": "application/json",
  };
  return new Response(upstreamBody, {
    status: upstreamStatus,
    headers: responseHeaders,
  });
}

const openai =
  LLM_VIA_SHROUD && SHROUD_SECRET
    ? createOpenAI({
        baseURL: `${SHROUD_URL.replace(/\/+$/, "")}/v1`,
        apiKey: "daemon-injected",
        fetch: proxyViaDaemon as typeof fetch,
      })
    : null;

const listSecretsTool = tool({
  description: "List secrets in the 1Claw vault (names only, no values)",
  parameters: z.object({ prefix: z.string().optional().describe("Path prefix filter") }),
  execute: async ({ prefix }) => {
    try {
      const vaultId = process.env.ONECLAW_VAULT_ID;
      if (!vaultId) return "No vault configured.";
      const resp = await claw.secrets.list(vaultId, prefix);
      const secrets = (resp as { data?: { secrets?: Array<{ path: string; type?: string }> } })
        .data?.secrets ?? [];
      return secrets.length
        ? secrets.map((s) => `  ${s.path} (${s.type ?? "generic"})`).join("\n")
        : "No secrets found.";
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      return `Error: ${msg}`;
    }
  },
});

const envTool = tool({
  description: "List 1Claw-related environment variables (values redacted)",
  parameters: z.object({}),
  execute: async () => {
    const vars = Object.keys(process.env)
      .filter((k) => k.startsWith("ONECLAW_"))
      .sort()
      .map((k) => `  ${k}=***`);
    return vars.length ? vars.join("\n") : "No ONECLAW_* vars set.";
  },
});

async function handleChat(message: string): Promise<string> {
  if (!openai) {
    return "No LLM configured. Re-run spawn with --agent-key ocv_... (and optional --llm-api-key). The host daemon injects Shroud credentials.";
  }

  conversationHistory.push({ role: "user", content: message });

  const { text } = await generateText({
    model: openai(MODEL),
    system:
      "You are a helpful AI agent running inside a secure 1Claw container. " +
      "You have access to the 1Claw SDK for vault secrets and multi-chain signing. " +
      "Be helpful and concise.",
    messages: conversationHistory,
    tools: { listSecrets: listSecretsTool, env: envTool },
  });

  conversationHistory.push({ role: "assistant", content: text });
  return text;
}

const server = createServer(async (req, res) => {
  if (req.url === "/health" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        status: "ok",
        framework: "typescript-sdk",
        llm_wired: LLM_VIA_SHROUD && !!SHROUD_SECRET,
        daemon_socket: DAEMON_SOCKET,
      }),
    );
    return;
  }

  if (req.url === "/chat" && req.method === "POST") {
    const chunks: Buffer[] = [];
    for await (const chunk of req) chunks.push(chunk as Buffer);
    const body = JSON.parse(Buffer.concat(chunks).toString()) as { message?: string };
    const message = (body.message ?? "").trim();

    if (!message) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "No message provided" }));
      return;
    }

    try {
      const response = await handleChat(message);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ response, framework: "typescript-sdk" }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: msg }));
    }
    return;
  }

  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(`<!DOCTYPE html>
<html><head><title>1Claw TypeScript Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw TypeScript Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Uses @1claw/sdk for vault access and multi-chain signing.
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>`);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`TypeScript SDK agent listening on http://0.0.0.0:${PORT}`);
});
