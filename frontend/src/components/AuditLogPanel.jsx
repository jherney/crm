export default function AuditLogPanel({ logs }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-slate-900/50 p-5 backdrop-blur-xl">
      <div className="mb-4 text-xs uppercase tracking-[0.24em] text-slate-500">Audit Log</div>
      <div className="space-y-3">
        {logs.map(log => (
          <div key={log.id} className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-medium text-white">{log.entityType} / {log.action}</div>
              <div className="text-xs text-slate-500">{log.createdAt}</div>
            </div>
            <div className="mt-1 text-xs uppercase tracking-[0.2em] text-cyan-300">actor: {log.actor}</div>
            <pre className="mt-3 overflow-auto whitespace-pre-wrap text-xs text-slate-300">{log.payload}</pre>
          </div>
        ))}
      </div>
    </section>
  );
}
