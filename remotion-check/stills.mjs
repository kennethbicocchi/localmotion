// Renders a few frames of a composition with a single bundle.
// Usage: node stills.mjs <project> <composition> <out_dir> <scale> [frames...]
// Without frames it only prints the metadata. On stdout: one JSON line with the result.
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [project, compId, outDir, scaleArg, ...frameArgs] = process.argv.slice(2);
const req = createRequire(path.join(project, "package.json"));
const load = async (name) => import(pathToFileURL(req.resolve(name)).href);

const { bundle } = await load("@remotion/bundler");
const { selectComposition, renderStill, openBrowser } = await load("@remotion/renderer");
const { enableTailwind } = await load("@remotion/tailwind-v4");

const serveUrl = await bundle({
  entryPoint: path.join(project, "src", "index.ts"),
  rootDir: project,
  publicDir: path.join(project, "public"),
  webpackOverride: (c) => enableTailwind(c),
  rspack: true,
  enableCaching: true,
});

// Readable error: name, message and the original source location instead of bundle.js line numbers
const explain = (e) => {
  const frames = (e?.stackFrame ?? [])
    .filter((f) => f.originalFileName && !f.originalFileName.includes("node_modules"))
    .slice(0, 4)
    .map((f) => `  at ${f.originalFunctionName ?? "?"} (${f.originalFileName}:${f.originalLineNumber}:${f.originalColumnNumber})`);
  return [`${e?.name ?? "Error"}: ${e?.message ?? String(e)}`.split("\n").slice(0, 6).join("\n"), ...frames].join("\n");
};

const browser = await openBrowser("chrome");
let composition;
try {
  composition = await selectComposition({ serveUrl, id: compId, puppeteerInstance: browser });
} catch (e) {
  await browser.close({ silent: true });
  process.stdout.write("\n@@ERROR@@" + JSON.stringify({ error: explain(e) }) + "\n");
  process.exit(0);
}
const meta = {
  id: composition.id,
  width: composition.width,
  height: composition.height,
  fps: composition.fps,
  durationInFrames: composition.durationInFrames,
};

const frames = frameArgs.map(Number).filter((f) => Number.isInteger(f));
const scale = Number(scaleArg) || 0.5;
const stills = [];
const errors = [];
if (frames.length) {
  mkdirSync(outDir, { recursive: true });
}
for (const frame of frames) {
  const f = Math.min(Math.max(0, frame), composition.durationInFrames - 1);
  const output = path.join(outDir, `${compId}-${String(f).padStart(5, "0")}.png`);
  try {
    await renderStill({
      serveUrl,
      composition,
      frame: f,
      output,
      scale,
      imageFormat: "png",
      overwrite: true,
      puppeteerInstance: browser,
    });
    stills.push({ frame: f, path: output });
  } catch (e) {
    errors.push({ frame: f, error: explain(e) });
  }
}
await browser.close({ silent: true });
process.stdout.write("\n@@RESULT@@" + JSON.stringify({ meta, stills, errors }) + "\n");
process.exit(0);
