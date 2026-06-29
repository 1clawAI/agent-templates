/**
 * Mastra agent pre-wired with 1Claw MCP for secrets and signing.
 *
 * LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
 * The container never sees raw API keys — they are injected by the host daemon.
 */

import { createServer } from "node:http";
import { Mastra } from "@mastra/core";
import { createOpenAI } from "@ai-sdk/openai";
import { generateText, tool } from "ai";
import { z } from "zod";

const SHROUD_URL = process.env.ONECLAW_SHROUD_URL ?? "https://shroud.1claw.xyz";
const LLM_VIA_SHROUD = process.env.ONECLAW_LLM_VIA_SHROUD === "true";
const PROVIDER = process.env.ONECLAW_SHROUD_PROVIDER ?? "openai";
const MODEL = process.env.ONECLAW_SHROUD_MODEL ?? "gpt-4o-mini";

const conversationHistory: { role: "user" | "assistant"; content: string }[] = [];

const openai = LLM_VIA_SHROUD
  ? createOpenAI({ baseURL: `${SHROUD_URL}/v1`, apiKey: "shroud-injected" })
  : null;

const mastra = new Mastra({});

const helloTool = tool({
  description: "Say hello to someone",
  parameters: z.object({ name: z.string().describe("Name to greet") }),
  execute: async ({ name }) =>
    `Hello, ${name}! I'm a Mastra agent running inside 1Claw.`,
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
      "You have access to tools for greeting and inspecting the environment.",
    messages: conversationHistory,
    tools: { hello: helloTool, env: envTool },
  });

  conversationHistory.push({ role: "assistant", content: text });
  return text;
}

const PORT = parseInt(process.env.CHAT_UI_PORT ?? "3000", 10);

const server = createServer(async (req, res) => {
  if (req.url === "/health" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", framework: "mastra", llm_wired: LLM_VIA_SHROUD }));
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
      res.end(JSON.stringify({ response, framework: "mastra" }));
    } catch (e: any) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(`<!DOCTYPE html>
<html><head><title>1Claw Mastra Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw Mastra Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>`);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Mastra agent listening on http://0.0.0.0:${PORT}`);
});
