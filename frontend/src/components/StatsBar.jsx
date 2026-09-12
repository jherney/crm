export default function StatsBar({ contacts }) {
  const companies = new Set(contacts.map((c) => c.company).filter(Boolean)).size;
  const tagged = contacts.filter((c) => c.tag && c.tag !== 'General').length;
  const favorites = contacts.filter((c) => c.favorite).length;

  const cards = [
    { label: 'Organizations', value: companies },
    { label: 'Tagged Profiles', value: tagged },
    { label: 'Priority Contacts', value: favorites }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {cards.map((card) => (
        <div key={card.label} className="rounded-2xl border border-white/10 bg-slate-900/50 p-5 backdrop-blur-xl">
          <div className="text-xs uppercase tracking-[0.3em] text-slate-500">{card.label}</div>
          <div className="mt-3 text-3xl font-semibold text-white">{card.value}</div>
        </div>
      ))}
    </div>
  );
}
