/**
 * ElizaOS agent pre-wired with 1Claw plugin for vault secrets and signing.
 *
 * LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
 * The container never sees raw API keys — they are injected by the host daemon.
 */

import { createServer } from "node:http";

const SHROUD_URL = process.env.ONECLAW_SHROUD_URL ?? "https://shroud.1claw.xyz";
const LLM_VIA_SHROUD = process.env.ONECLAW_LLM_VIA_SHROUD === "true";
const PROVIDER = process.env.ONECLAW_SHROUD_PROVIDER ?? "openai";
const MODEL = process.env.ONECLAW_SHROUD_MODEL ?? "gpt-4o-mini";
const PORT = parseInt(process.env.CHAT_UI_PORT ?? "3000", 10);

const conversationHistory: { role: "user" | "assistant"; content: string }[] = [];

/**
 * Minimal chat handler using OpenAI-compatible API through Shroud.
 * Replace with a full ElizaOS AgentRuntime for production use.
 */
async function handleChat(message: string): Promise<string> {
  if (!LLM_VIA_SHROUD) {
    return "No LLM configured. Use --llm-api-key or enable Token Billing.";
  }

  conversationHistory.push({ role: "user", content: message });

  const resp = await fetch(`${SHROUD_URL}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer shroud-injected" },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        {
          role: "system" as const,
          content:
            "You are an ElizaOS character running inside a secure 1Claw container. " +
            "The @1claw/plugin-elizaos plugin gives you vault access and multi-chain signing. " +
            "Be helpful and concise.",
        },
        ...conversationHistory,
      ],
    }),
  });

  if (!resp.ok) throw new Error(`LLM error: ${resp.status} ${await resp.text()}`);

  const data = await resp.json() as any;
  const text = data.choices?.[0]?.message?.content ?? "No response from LLM.";
  conversationHistory.push({ role: "assistant", content: text });
  return text;
}

const server = createServer(async (req, res) => {
  if (req.url === "/health" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", framework: "elizaos", llm_wired: LLM_VIA_SHROUD }));
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
      res.end(JSON.stringify({ response, framework: "elizaos" }));
    } catch (e: any) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(`<!DOCTYPE html>
<html><head><title>1Claw ElizaOS Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw ElizaOS Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
The @1claw/plugin-elizaos plugin provides 8 actions for vault secrets and multi-chain signing.
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>`);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`ElizaOS agent listening on http://0.0.0.0:${PORT}`);
});
