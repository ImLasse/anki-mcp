#!/usr/bin/env node
// Dependency-free UTF-8 stdio transport. Only connects to Anki on loopback.
"use strict";
const http = require("node:http");
const fs = require("node:fs");
const readline = require("node:readline");

const options = process.argv.slice(2);
function option(name, fallback) {
  const index = options.indexOf(name);
  return index < 0 ? fallback : options[index + 1];
}
const port = Number(option("--port", "8766"));
let token;
try {
  if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error();
  token = fs.readFileSync(option("--token-file", ""), "utf8").trim();
  if (!/^[A-Za-z0-9_-]{32,512}$/.test(token)) throw new Error();
} catch {
  process.stderr.write("Anki MCP: check port and select the token file shown in Anki.\n");
  process.exit(1);
}
const MAX_BYTES = 32 * 1024 * 1024;
function send(value) {
  process.stdout.write(JSON.stringify(value) + "\n");
}
function forward(message) {
  return new Promise((resolve, reject) => {
    const body = Buffer.from(JSON.stringify(message));
    if (body.length > MAX_BYTES) return reject(new Error("Request exceeds 32 MiB"));
    const req = http.request({
      hostname: "127.0.0.1", port, path: "/mcp", method: "POST", agent: false,
      headers: { "Authorization": "Bearer " + token, "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream", "Content-Length": body.length },
    }, (res) => {
      let size = 0;
      const chunks = [];
      res.on("error", reject);
      res.on("data", chunk => {
        size += chunk.length;
        if (size > MAX_BYTES) res.destroy(new Error("Response exceeds 32 MiB"));
        else chunks.push(chunk);
      });
      res.on("end", () => {
        if (res.statusCode === 202 || res.statusCode === 204) return resolve(null);
        if (res.statusCode !== 200) return reject(new Error("Anki HTTP " + res.statusCode));
        try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8"))); }
        catch { reject(new Error("Invalid Anki response")); }
      });
    });
    // No retries: the collection may already have changed after a timeout.
    req.setTimeout(120000, () => req.destroy(new Error("Anki timed out; inspect targets before retrying")));
    req.on("error", error => reject(new Error(error.code ? "Anki connection " + error.code : error.message)));
    req.end(body);
  });
}
async function main() {
  const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of input) {
    if (!line.trim()) continue;
    let message;
    try {
      if (Buffer.byteLength(line) > MAX_BYTES) throw new Error();
      message = JSON.parse(line);
      if (!message || Array.isArray(message) || typeof message !== "object") throw new Error();
    } catch {
      send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Invalid JSON-RPC input" } });
      continue;
    }
    try {
      const result = await forward(message);
      if (Object.hasOwn(message, "id") && result) send(result);
    } catch (error) {
      if (Object.hasOwn(message, "id")) send({ jsonrpc: "2.0", id: message.id,
        error: { code: -32000, message: error.message + ". Check Anki and its open profile; inspect state before retrying." } });
    }
  }
}
main().catch(() => { process.stderr.write("Anki MCP transport stopped.\n"); process.exitCode = 1; });
