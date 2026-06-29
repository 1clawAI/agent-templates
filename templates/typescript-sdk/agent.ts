/**
 * Plain TypeScript agent using @1claw/sdk for vault access and signing,
 * with Vercel AI SDK for LLM interaction through Shroud.
 *
 * LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
 * The container never sees raw API keys — they are injected by the host daemon.
 */

import { createServer } from "node:http";
import { OneclawClient } from "@1claw/sdk";
import { createOpenAI } from "@ai-sdk/openai";
import { generateText, tool } from "ai";
import { z } from "zod";

const SHROUD_URL = process.env.ONECLAW_SHROUD_URL ?? "https://shroud.1claw.xyz";
const LLM_VIA_SHROUD = process.env.ONECLAW_LLM_VIA_SHROUD === "true";
const MODEL = process.env.ONECLAW_SHROUD_MODEL ?? "gpt-4o-mini";
const PORT = parseInt(process.env.CHAT_UI_PORT ?? "3000", 10);

const conversationHistory: { role: "user" | "assistant"; content: string }[] = [];

const claw = new OneclawClient({
  apiKey: process.env.ONECLAW_AGENT_API_KEY,
  agentId: process.env.ONECLAW_AGENT_ID,
  baseUrl: process.env.ONECLAW_BASE_URL ?? "https://api.1claw.xyz",
});

const openai = LLM_VIA_SHROUD
  ? createOpenAI({ baseURL: `${SHROUD_URL}/v1`, apiKey: "shroud-injected" })
  : null;

const listSecretsTool = tool({
  description: "List secrets in the 1Claw vault (names only, no values)",
  parameters: z.object({ prefix: z.string().optional().describe("Path prefix filter") }),
  execute: async ({ prefix }) => {
    try {
      const vaultId = process.env.ONECLAW_VAULT_ID;
      if (!vaultId) return "No vault configured.";
      const resp = await claw.secrets.list(vaultId, prefix);
      const secrets = (resp as any).data?.secrets ?? [];
      return secrets.length
        ? secrets.map((s: any) => `  ${s.path} (${s.type ?? "generic"})`).join("\n")
        : "No secrets found.";
    } catch (e: any) {
      return `Error: ${e.message}`;
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
    return "No LLM configured. Use --llm-api-key or enable Token Billing.";
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
      JSON.stringify({ status: "ok", framework: "typescript-sdk", llm_wired: LLM_VIA_SHROUD }),
    );
    return;
  }

  if (req.url === "/chat" && req.method === "POST") {
    const chunks: Buffer[] = [];
    for await (const chunk of req) chunks.push(chunk as Buffer);
    const body = JSON.parse(Buffer.concat(chunks).toString());
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
    } catch (e: any) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
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
