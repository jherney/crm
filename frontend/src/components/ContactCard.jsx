export default function ContactCard({ contact, onEdit, onDelete, onRestore, onPurge, onInspect }) {
  const deleted = Boolean(contact.deletedAt);

  return (
    <div className={`rounded-3xl border p-5 backdrop-blur-xl ${deleted ? 'border-rose-400/20 bg-rose-500/10' : 'border-white/10 bg-slate-900/50'}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-xl font-semibold text-white">{contact.name || 'Unnamed Contact'}</h3>
            {contact.favorite && <span className="rounded-full border border-fuchsia-400/30 bg-fuchsia-500/20 px-3 py-1 text-xs text-fuchsia-200">Priority</span>}
            {deleted && <span className="rounded-full border border-rose-400/30 bg-rose-500/20 px-3 py-1 text-xs text-rose-200">Deleted</span>}
          </div>
          <p className="mt-2 text-sm text-slate-400">{contact.metadata?.company || contact.metadata?.department || ''}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(contact.tags || []).map(tag => (
              <span key={tag} className="rounded-full border border-cyan-400/30 bg-cyan-500/20 px-3 py-1 text-xs text-cyan-200">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <button onClick={() => onInspect(contact)} className="rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300">Open</button>
      </div>

      <div className="mt-5 grid gap-2 text-sm text-slate-300">
        <div><span className="text-slate-500">Email:</span> {contact.email || 'No signal'}</div>
        <div><span className="text-slate-500">Phone:</span> {contact.phone || 'No signal'}</div>
        <div><span className="text-slate-500">Notes:</span> {contact.notes || contact.metadata?.notes || 'No notes stored.'}</div>
      </div>

      <div className="mt-4 rounded-2xl border border-white/10 bg-black/10 p-3">
        <div className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-500">Custom Fields</div>
        <pre className="overflow-auto whitespace-pre-wrap text-xs text-slate-300">{JSON.stringify(contact.metadata || {}, null, 2)}</pre>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        {!deleted && (
          <>
            <button onClick={() => onEdit(contact)} className="rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-100">Edit</button>
            <button onClick={() => onDelete(contact.id)} className="rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-2 text-sm text-rose-100">Soft Delete</button>
          </>
        )}
        {deleted && (
          <>
            <button onClick={() => onRestore(contact.id)} className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-100">Restore</button>
            <button onClick={() => onPurge(contact.id)} className="rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-2 text-sm text-rose-100">Purge</button>
          </>
        )}
      </div>
    </div>
  );
}
