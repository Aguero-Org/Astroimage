/** Render an Arc diagram SVG with a named theme via the @arach/arc MCP server.
 *
 * The `arc` CLI does not expose theme/mode rendering, so this script calls
 * the `render_svg` MCP tool (theme + mode supported) over stdio. Requires
 * node >= 22, npx and network access (downloads @arach/arc-mcp on first use).
 *
 * Usage (from repo root):
 *   node docs/architecture/render-themed-svg.mjs \
 *     docs/architecture/entrega1-us5.arc.json \
 *     docs/architecture/entrega1-us5.svg tactical light transparent off
 *
 * Args: <diagram.json> <out.svg> [theme] [mode] [background] [grid]
 *   background: CSS color, "transparent", or "theme" (default) for the theme canvas.
 *   grid: "on", "off", or "theme" (default) to force the background grid.
 */

import { spawn } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";

const [diagramPath, outPath, theme = "tactical", mode = "light", background = "theme", grid = "theme"] =
  process.argv.slice(2);
if (!diagramPath || !outPath) {
  console.error("usage: render-themed-svg.mjs <diagram.json> <out.svg> [theme] [mode]");
  process.exit(2);
}

const child = spawn("npx -y @arach/arc-mcp", [], { stdio: ["pipe", "pipe", "inherit"], shell: true });

let buf = "";
let id = 0;
const pending = new Map();
child.stdout.on("data", (chunk) => {
  buf += chunk.toString();
  const lines = buf.split("\n");
  buf = lines.pop();
  for (const line of lines) {
    if (!line.trim()) continue;
    const msg = JSON.parse(line);
    if (msg.id !== undefined && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  }
});

function req(method, params) {
  return new Promise((resolve) => {
    const msgId = ++id;
    pending.set(msgId, resolve);
    child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id: msgId, method, params })}\n`);
  });
}

await req("initialize", {
  protocolVersion: "2024-11-05",
  capabilities: {},
  clientInfo: { name: "render-themed-svg", version: "1.0.0" },
});
child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" })}\n`);

const diagram = JSON.parse(readFileSync(diagramPath, "utf8"));
const args = { diagram, theme, mode };
if (background !== "theme") args.backgroundColor = background;
if (grid !== "theme") args.includeGrid = grid === "on";
const res = await req("tools/call", { name: "render_svg", arguments: args });
child.kill();

if (res.error) {
  console.error(`MCP error: ${JSON.stringify(res.error).slice(0, 400)}`);
  process.exit(1);
}
const parts = res.result.content.map((c) => c.text ?? JSON.stringify(c)).join("\n");
const match = parts.match(/<svg[\s\S]*<\/svg>/);
if (!match) {
  console.error(`render_svg returned no SVG: ${parts.slice(0, 400)}`);
  process.exit(1);
}
const svg = flattenAlphaFills(match[0]);
writeFileSync(outPath, svg, "utf8");
console.log(`wrote ${outPath} (${svg.length} bytes, theme=${theme} mode=${mode} background=${background} grid=${grid})`);

// GitHub's markdown preview shows the page through any fill that still has
// an alpha channel, so a white canvas rect is not enough in dark mode.
function flattenAlphaFills(svg) {
  const withPlate = svg.replace(
    "<svg ",
    '<svg style="background-color:#ffffff" ',
  );
  return withPlate.replace(
    /fill="#([0-9a-fA-F]{6})([0-9a-fA-F]{2})"/g,
    (_full, rgb, alpha) => `fill="${mixOnWhite(rgb, alpha)}"`,
  );
}

function mixOnWhite(rgb, alpha) {
  const amount = Number.parseInt(alpha, 16) / 255;
  const mix = (channel) =>
    Math.round(channel * amount + 255 * (1 - amount))
      .toString(16)
      .padStart(2, "0");
  return `#${mix(Number.parseInt(rgb.slice(0, 2), 16))}${mix(Number.parseInt(rgb.slice(2, 4), 16))}${mix(Number.parseInt(rgb.slice(4, 6), 16))}`;
}
