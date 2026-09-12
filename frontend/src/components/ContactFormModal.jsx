import { useEffect, useState } from 'react';

const emptyState = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  company: '',
  notes: '',
  favorite: false,
  customFieldsText: '{\n  "source": "manual"\n}',
  tagIds: []
};

export default function ContactFormModal({ open, onClose, onSubmit, initialData, tags }) {
  const [form, setForm] = useState(emptyState);
  const [jsonError, setJsonError] = useState('');

  useEffect(() => {
    if (!open) return;
    if (initialData) {
      setForm({
        firstName: initialData.firstName || '',
        lastName: initialData.lastName || '',
        email: initialData.email || '',
        phone: initialData.phone || '',
        company: initialData.company || '',
        notes: initialData.notes || '',
        favorite: Boolean(initialData.favorite),
        customFieldsText: JSON.stringify(initialData.customFields || initialData.metadata || {}, null, 2),
        tagIds: initialData.tags || []
      });
    } else {
      setForm(emptyState);
    }
    setJsonError('');
  }, [open, initialData]);

  if (!open) return null;

  function setField(key, value) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  function toggleTag(tag) {
    setForm(prev => ({
      ...prev,
      tagIds: prev.tagIds.includes(tag) ? prev.tagIds.filter(id => id !== tag) : [...prev.tagIds, tag]
    }));
  }

  function submit(e) {
    e.preventDefault();
    try {
      const customFields = JSON.parse(form.customFieldsText || '{}');
      setJsonError('');
      onSubmit({
        firstName: form.firstName,
        lastName: form.lastName,
        email: form.email,
        phone: form.phone,
        company: form.company,
        notes: form.notes,
        favorite: form.favorite,
        customFields,
        tagIds: form.tagIds
      });
    } catch {
      setJsonError('Custom fields must be valid JSON.');
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 backdrop-blur-sm">
      <form onSubmit={submit} className="max-h-[92vh] w-full max-w-4xl overflow-auto rounded-3xl border border-cyan-400/20 bg-slate-900/95 p-6 shadow-neon">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-cyan-300">Identity Editor</div>
            <h2 className="mt-2 text-2xl font-semibold text-white">{initialData ? 'Edit Contact' : 'Create Contact'}</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-xl border border-white/10 px-3 py-2 text-slate-300">Close</button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="First name" value={form.firstName} onChange={(e) => setField('firstName', e.target.value)} required />
          <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Last name" value={form.lastName} onChange={(e) => setField('lastName', e.target.value)} required />
          <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Email" value={form.email} onChange={(e) => setField('email', e.target.value)} />
          <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Phone" value={form.phone} onChange={(e) => setField('phone', e.target.value)} />
          <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white md:col-span-2" placeholder="Company" value={form.company} onChange={(e) => setField('company', e.target.value)} />
        </div>

        <textarea className="mt-4 min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Notes" value={form.notes} onChange={(e) => setField('notes', e.target.value)} />
        <label className="mt-4 flex items-center gap-3 text-sm text-slate-300">
          <input type="checkbox" checked={form.favorite} onChange={(e) => setField('favorite', e.target.checked)} />
          Mark as priority contact
        </label>

        <div className="mt-6">
          <div className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-500">Tags</div>
          <div className="flex flex-wrap gap-2">
            {tags.map(tag => {
              const active = form.tagIds.includes(tag);
              return (
                <button
                  type="button"
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`rounded-full border px-3 py-2 text-sm ${active ? 'text-white border-cyan-400/40 bg-cyan-400/20' : 'text-slate-300 border-white/10 bg-white/5'}`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-6">
          <div className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-500">Custom Fields JSON</div>
          <textarea className="min-h-52 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 font-mono text-sm text-white" value={form.customFieldsText} onChange={(e) => setField('customFieldsText', e.target.value)} />
          {jsonError && <div className="mt-2 text-sm text-rose-300">{jsonError}</div>}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-2xl border border-white/10 px-4 py-3 text-slate-300">Cancel</button>
          <button type="submit" className="rounded-2xl border border-cyan-300/30 bg-cyan-400/20 px-5 py-3 font-medium text-cyan-100">
            {initialData ? 'Save Changes' : 'Create Contact'}
          </button>
        </div>
      </form>
    </div>
  );
}
