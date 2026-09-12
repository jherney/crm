export default function Toolbar({ search, setSearch, includeDeleted, setIncludeDeleted, onCreate, onExport, onImport }) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-slate-900/50 p-4 backdrop-blur-xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex-1">
          <label className="mb-2 block text-xs uppercase tracking-[0.28em] text-slate-500">Search Matrix</label>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, phone, company, notes, or custom fields"
            className="w-full rounded-2xl border border-cyan-400/20 bg-slate-950/70 px-4 py-3 text-slate-100 outline-none"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={onCreate} className="rounded-2xl border border-cyan-300/30 bg-cyan-400/20 px-5 py-3 font-medium text-cyan-100">+ New Contact</button>
          <button onClick={onExport} className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-slate-100">Export CSV</button>
          <label className="cursor-pointer rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-slate-100">
            Import CSV
            <input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => onImport(e.target.files?.[0])} />
          </label>
        </div>
      </div>

      <label className="flex items-center gap-3 text-sm text-slate-300">
        <input type="checkbox" checked={includeDeleted} onChange={(e) => setIncludeDeleted(e.target.checked)} />
        Include deleted contacts
      </label>
    </div>
  );
}
