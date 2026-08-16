import { execSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = join(webRoot, "..");

function gitShort() {
  try {
    return execSync("git rev-parse --short HEAD", { cwd: repoRoot, stdio: ["ignore", "pipe", "ignore"] })
      .toString()
      .trim();
  } catch {
    return "";
  }
}

const id = process.env.GITHUB_SHA?.slice(0, 7) || gitShort() || `dev-${Date.now().toString(36)}`;
const builtAt = new Date().toISOString();
const publicDir = join(webRoot, "public");
mkdirSync(publicDir, { recursive: true });

const version = {
  id,
  built_at: builtAt,
  name: "Brasil Real",
};
writeFileSync(join(publicDir, "version.json"), `${JSON.stringify(version, null, 2)}\n`);

let sw = readFileSync(join(webRoot, "pwa/sw.js"), "utf8");
sw = sw.replaceAll("__BR_BUILD__", id).replaceAll("__BR_BUILT_AT__", builtAt);
writeFileSync(join(publicDir, "sw.js"), sw);
console.log(`PWA build ${id} @ ${builtAt}`);
