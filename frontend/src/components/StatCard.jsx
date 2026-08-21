export default function StatCard({ label, value, accent = "from-amber-400 to-orange-600" }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl backdrop-blur">
      <div className={`mb-4 h-1.5 w-16 rounded-full bg-gradient-to-r ${accent}`} />
      <p className="text-sm uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-3 font-display text-3xl text-white">{value}</p>
    </div>
  );
}
