import { useState } from "react";
import { api } from "../lib/api";

export default function AssistantPanel({ context }) {
  const [question, setQuestion] = useState("What are the highest-risk modules and how should I reduce risk first?");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    setLoading(true);
    try {
      const response = await api.askAI(question, context);
      setAnswer(response.answer);
    } catch (error) {
      setAnswer(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-[2rem] border border-white/10 bg-slate-900/70 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-amber-300">Developer Assistant</p>
          <h2 className="mt-2 font-display text-2xl text-white">Gemini 2.5 Flash copilot for quality insights</h2>
        </div>
        <button onClick={handleAsk} className="rounded-full bg-amber-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-400">
          {loading ? "Thinking..." : "Ask AI"}
        </button>
      </div>
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        className="mt-5 min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-slate-100 outline-none"
      />
      <div className="mt-5 whitespace-pre-wrap rounded-2xl border border-amber-400/20 bg-amber-100/5 p-4 text-slate-200">
        {answer || "Ask for bug fixes, test suggestions, code explanations, or refactoring guidance."}
      </div>
    </section>
  );
}
