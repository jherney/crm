export default function Sidebar({ contacts, reminders, deletedCount }) {
  const favorites = contacts.filter(c => c.favorite).length;
  const openReminders = reminders.filter(r => r.status === 'open').length;

  return (
    <aside className="w-full max-w-xs rounded-3xl border border-cyan-400/20 bg-slate-900/60 p-6 shadow-neon backdrop-blur-xl">
      <div className="mb-8">
        <div className="mb-2 inline-flex rounded-full border border-cyan-400/30 px-3 py-1 text-xs uppercase tracking-[0.32em] text-cyan-300">
          Neural Grid
        </div>
        <h1 className="text-3xl font-semibold text-white">Contact Nexus</h1>
        <p className="mt-3 text-sm text-slate-400">
          Search, timeline, reminders, recovery, and audit visibility in one console.
        </p>
      </div>

      <div className="grid gap-4">
        <Stat label="Live Contacts" value={contacts.length} />
        <Stat label="Priority Signals" value={favorites} />
        <Stat label="Open Reminders" value={openReminders} />
        <Stat label="Recycle Bin" value={deletedCount} />
      </div>
    </aside>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-xs uppercase tracking-[0.28em] text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-white">{value}</div>
    </div>
  );
}
