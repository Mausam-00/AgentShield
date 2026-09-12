import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import path from "node:path";

// Runs the AgentShield "before -> after remediation" driver on the server.
// Nothing is executed against a target; the two demo agent definitions are
// read-only inputs. Requires the Node runtime (child_process), not edge.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const REPO_ROOT = path.join(process.cwd(), "..");
const DRIVER = path.join(REPO_ROOT, "scripts", "agentshield_before_after.py");
const PYTHON = process.env.AGENTSHIELD_PYTHON || (process.platform === "win32" ? "python" : "python3");
const TIMEOUT_MS = Number(process.env.AGENTSHIELD_ENGINE_TIMEOUT_MS || 60_000);

const MAX_CONCURRENT = 2;
let inFlight = 0;

function runDriver(): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(PYTHON, [DRIVER, "--stdout"], { cwd: REPO_ROOT, windowsHide: true });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGKILL");
      reject(new Error(`driver timed out after ${TIMEOUT_MS}ms`));
    }, TIMEOUT_MS);
    child.stdout.on("data", (d) => (stdout += d.toString()));
    child.stderr.on("data", (d) => (stderr += d.toString()));
    child.on("error", (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(err);
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (stderr.trim()) console.error(`[agentshield-showcase] ${stderr.trim()}`);
      if (code === 0) resolve(stdout);
      else reject(new Error(`driver exited with code ${code}: ${stderr || stdout}`));
    });
  });
}

export async function GET() {
  if (inFlight >= MAX_CONCURRENT) {
    return NextResponse.json(
      { error: "The showcase engine is busy. Please retry in a moment." },
      { status: 429, headers: { "Retry-After": "5" } },
    );
  }
  inFlight += 1;
  try {
    const stdout = await runDriver();
    const line = stdout.trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
    const data = JSON.parse(line);
    return NextResponse.json({ data, live: true });
  } catch (err) {
    // The page falls back to the baked static JSON, so return a soft error.
    console.error("[agentshield-showcase] live run failed:", err);
    return NextResponse.json(
      { error: "Live engine unavailable; showing the last generated result." },
      { status: 503 },
    );
  } finally {
    inFlight -= 1;
  }
}
