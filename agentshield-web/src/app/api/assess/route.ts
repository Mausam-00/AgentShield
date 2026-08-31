import { NextRequest, NextResponse } from "next/server";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

// The AgentShield engine is Python; run it on the server, nothing is executed
// against a target. Requires Node runtime (child_process + fs), not edge.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_BYTES = 512 * 1024; // 512 KB is ample for an agent definition.
// Repo root is the parent of the Next.js app directory (process.cwd()).
const REPO_ROOT = path.join(process.cwd(), "..");
const REPORT_SCRIPT = path.join(REPO_ROOT, "scripts", "agentshield_report.py");
const PYTHON = process.env.AGENTSHIELD_PYTHON || (process.platform === "win32" ? "python" : "python3");

// Resource guards for the unauthenticated public endpoint: bound how long the
// engine may run and how many assessments may run concurrently, so a hostile or
// pathological upload cannot exhaust CPU/memory or pile up processes.
const ENGINE_TIMEOUT_MS = Number(process.env.AGENTSHIELD_ENGINE_TIMEOUT_MS || 60_000);
const MAX_CONCURRENT = Number(process.env.AGENTSHIELD_MAX_CONCURRENT || 2);
let inFlight = 0;

type EngineSummary = {
  subject: string;
  assurance_posture: string;
  assurance_score: number;
  runtime_decision: string;
  redteam_posture: string;
  defense_coverage: number | null;
  residual_exposure: number | null;
  rai_posture: string;
  enrichment?: { status?: string; model?: string; prompt_version?: string; cache_key?: string };
  html_path: string;
};

function runEngine(mdPath: string, outPath: string): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(PYTHON, [REPORT_SCRIPT, mdPath, outPath], {
      cwd: REPO_ROOT,
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGKILL");
      reject(new Error(`engine timed out after ${ENGINE_TIMEOUT_MS}ms`));
    }, ENGINE_TIMEOUT_MS);
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
      // Surface engine diagnostics (e.g. LLM enrichment skip reasons) to the
      // server logs; they are otherwise swallowed on a successful run.
      if (stderr.trim()) console.error(`[agentshield-engine] ${stderr.trim()}`);
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(`engine exited with code ${code}: ${stderr || stdout}`));
    });
  });
}

export async function POST(req: NextRequest) {
  if (inFlight >= MAX_CONCURRENT) {
    return NextResponse.json(
      { error: "The assessment service is busy. Please retry in a moment." },
      { status: 429, headers: { "Retry-After": "5" } },
    );
  }
  inFlight += 1;
  let workDir: string | null = null;
  try {
    const form = await req.formData();
    const file = form.get("file");
    if (!(file instanceof File)) {
      return NextResponse.json({ error: "No file uploaded. Attach an agent .md definition." }, { status: 400 });
    }
    if (!/\.(md|markdown|txt)$/i.test(file.name)) {
      return NextResponse.json({ error: "Unsupported file type. Upload a Markdown (.md) agent definition." }, { status: 415 });
    }
    const bytes = Buffer.from(await file.arrayBuffer());
    if (bytes.length === 0) {
      return NextResponse.json({ error: "The uploaded file is empty." }, { status: 400 });
    }
    if (bytes.length > MAX_BYTES) {
      return NextResponse.json({ error: "File too large (max 512 KB)." }, { status: 413 });
    }

    workDir = await mkdtemp(path.join(tmpdir(), "agentshield-"));
    const mdPath = path.join(workDir, "agent.md");
    const outPath = path.join(workDir, `report-${randomUUID()}.html`);
    await writeFile(mdPath, bytes);

    const { stdout } = await runEngine(mdPath, outPath);
    const line = stdout.trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
    const summary = JSON.parse(line) as EngineSummary;
    const html = await readFile(outPath, "utf-8");

    // Surface how the LLM narrative was sourced (cache hit vs a fresh, possibly
    // divergent model call) so web/CLI parity issues are observable at a glance.
    const enrichStatus = summary.enrichment?.status ?? "unknown";
    console.log(
      `[agentshield-assess] subject="${summary.subject}" enrichment=${enrichStatus} ` +
        `model=${summary.enrichment?.model ?? "-"} prompt=${summary.enrichment?.prompt_version ?? "-"}`,
    );

    return NextResponse.json(
      { summary, html },
      { headers: { "X-Enrichment": enrichStatus } },
    );
  } catch (err) {
    // Log the full diagnostic server-side only; never leak internal paths,
    // stack traces, or engine stderr to the client.
    console.error("[agentshield-assess] request failed:", err);
    const isMissingPython = err instanceof Error && /ENOENT/.test(err.message);
    const isTimeout = err instanceof Error && /timed out/.test(err.message);
    const message = isMissingPython
      ? "The assessment engine is unavailable. Please try again later."
      : isTimeout
        ? "The assessment took too long and was stopped. Try a smaller definition."
        : "Assessment failed. Please check your file and try again.";
    const status = isTimeout ? 504 : 500;
    return NextResponse.json({ error: message }, { status });
  } finally {
    inFlight -= 1;
    if (workDir) await rm(workDir, { recursive: true, force: true }).catch(() => {});
  }
}
