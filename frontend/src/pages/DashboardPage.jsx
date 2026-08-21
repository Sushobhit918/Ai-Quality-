import { useState } from "react";
import { api } from "../lib/api";
import StatCard from "../components/StatCard";
import AssistantPanel from "../components/AssistantPanel";

export default function DashboardPage() {
  const [projectPath, setProjectPath] = useState("Dataset/express");
  const [state, setState] = useState({
    analysis: null,
    predictions: [],
    bugReports: [],
    loading: false,
    error: ""
  });

  async function runAnalysis() {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [analysisResult, predictionResult, bugResult] = await Promise.all([
        api.analyze(projectPath),
        api.predictDefects(projectPath),
        api.generateBugs(projectPath)
      ]);
      setState({
        analysis: analysisResult,
        predictions: predictionResult.predictions,
        bugReports: bugResult.bug_reports,
        loading: false,
        error: ""
      });
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error: error.message }));
    }
  }

  const summary = state.analysis?.analysis?.summary;
  const testIntel = state.analysis?.test_intelligence;
  const highRisk = state.predictions.filter((item) => item.is_high_risk).length;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.25),_transparent_30%),linear-gradient(135deg,_#020617,_#111827_45%,_#1e293b)] px-4 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <section className="rounded-[2rem] border border-white/10 bg-black/20 p-8 shadow-[0_40px_120px_rgba(15,23,42,0.55)] backdrop-blur">
          <p className="text-sm uppercase tracking-[0.45em] text-amber-300">AI Quality Platform</p>
          <div className="mt-4 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <h1 className="font-display text-5xl leading-tight text-white">Defect prediction, code intelligence, and AI debugging in one platform.</h1>
              <p className="mt-4 max-w-2xl text-lg text-slate-300">
                Analyze multi-language repositories, surface risky modules, inspect test gaps, generate bug reports, and ask Gemini for targeted engineering guidance.
              </p>
            </div>
            <div className="w-full max-w-xl rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
              <label className="text-sm uppercase tracking-[0.2em] text-slate-400">Repository Path</label>
              <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                <input
                  value={projectPath}
                  onChange={(event) => setProjectPath(event.target.value)}
                  className="flex-1 rounded-full border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                />
                <button onClick={runAnalysis} className="rounded-full bg-emerald-400 px-6 py-3 font-semibold text-slate-950 hover:bg-emerald-300">
                  {state.loading ? "Running..." : "Analyze Repo"}
                </button>
              </div>
              {state.error ? <p className="mt-3 text-sm text-rose-300">{state.error}</p> : null}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Files Scanned" value={summary?.total_loc ? state.analysis.analysis.file_count : "0"} />
          <StatCard label="Total LOC" value={summary?.total_loc ?? "0"} accent="from-emerald-400 to-lime-500" />
          <StatCard label="High Risk Modules" value={highRisk} accent="from-rose-400 to-red-600" />
          <StatCard label="Coverage Estimate" value={testIntel ? `${testIntel.coverage_estimate}%` : "0%"} accent="from-cyan-400 to-blue-500" />
        </section>

        <section className="mt-8 grid gap-8 xl:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-8">
            <div className="rounded-[2rem] border border-white/10 bg-slate-900/70 p-6">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-2xl">Risk Heatmap</h2>
                <span className="text-sm text-slate-400">{state.predictions.length} modules scored</span>
              </div>
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {state.predictions.slice(0, 12).map((item) => (
                  <div
                    key={item.row_index}
                    className={`rounded-2xl p-4 ${
                      item.risk_level === "high"
                        ? "border border-red-400/30 bg-red-500/20"
                        : item.risk_level === "medium"
                          ? "border border-amber-400/30 bg-amber-500/20"
                          : "border border-emerald-400/30 bg-emerald-500/20"
                    }`}
                  >
                    <p className="text-sm text-slate-300">Module #{item.row_index + 1}</p>
                    <p className="mt-2 text-2xl font-semibold">{(item.defect_probability * 100).toFixed(1)}%</p>
                    <p className="mt-1 text-sm uppercase tracking-[0.2em] text-slate-300">{item.risk_level}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-slate-900/70 p-6">
              <h2 className="font-display text-2xl">Bug Reports</h2>
              <div className="mt-5 space-y-4">
                {state.bugReports.slice(0, 6).map((bug) => (
                  <article key={bug.title} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="text-lg font-semibold">{bug.title}</h3>
                      <span className="rounded-full bg-roseclay px-3 py-1 text-xs uppercase tracking-[0.2em]">{bug.severity}</span>
                    </div>
                    <p className="mt-3 text-slate-300">{bug.suggested_fix}</p>
                  </article>
                ))}
                {!state.bugReports.length ? <p className="text-slate-400">Run analysis to generate structured bug reports.</p> : null}
              </div>
            </div>
          </div>

          <div className="space-y-8">
            <div className="rounded-[2rem] border border-white/10 bg-slate-900/70 p-6">
              <h2 className="font-display text-2xl">Test Intelligence</h2>
              <div className="mt-5 space-y-4 text-slate-200">
                <p>Jest: {testIntel?.framework_counts?.jest ?? 0}</p>
                <p>Pytest: {testIntel?.framework_counts?.pytest ?? 0}</p>
                <p>JUnit: {testIntel?.framework_counts?.junit ?? 0}</p>
                <p>Missing edge cases: {testIntel?.missing_edge_cases?.length ?? 0}</p>
              </div>
            </div>
            <AssistantPanel context={{ analysis: state.analysis, predictions: state.predictions, bugReports: state.bugReports }} />
          </div>
        </section>
      </div>
    </main>
  );
}
