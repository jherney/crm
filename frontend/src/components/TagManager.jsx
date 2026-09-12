import { useState } from 'react';

export default function TagManager({ tags, onCreateTag }) {
  const [name, setName] = useState('');
  const [color, setColor] = useState('#22d3ee');

  async function submit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    await onCreateTag({ name: name.trim(), color });
    setName('');
    setColor('#22d3ee');
  }

  return (
    <section className="rounded-3xl border border-white/10 bg-slate-900/50 p-5 backdrop-blur-xl">
      <div className="mb-4 text-xs uppercase tracking-[0.24em] text-slate-500">Tag Manager</div>
      <form onSubmit={submit} className="grid gap-3 md:grid-cols-[1fr_140px_auto]">
        <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="New tag name" value={name} onChange={(e) => setName(e.target.value)} />
        <input type="color" className="h-12 rounded-2xl border border-white/10 bg-slate-950/70 px-2 py-2" value={color} onChange={(e) => setColor(e.target.value)} />
        <button className="rounded-2xl border border-cyan-300/30 bg-cyan-400/20 px-5 py-3 text-cyan-100">Add Tag</button>
      </form>
      <div className="mt-4 flex flex-wrap gap-2">
        {tags.map(tag => (
          <span key={tag} className="rounded-full border border-cyan-400/30 bg-cyan-500/20 px-3 py-2 text-sm text-cyan-200">
            {tag}
          </span>
        ))}
      </div>
    </section>
  );
}
