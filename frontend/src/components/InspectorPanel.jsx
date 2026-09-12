import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export default function InspectorPanel({ contact, onClose, onRefresh }) {
  const [activities, setActivities] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [activityForm, setActivityForm] = useState({ type: 'note', subject: '', body: '' });
  const [reminderForm, setReminderForm] = useState({ title: '', dueAt: '', notes: '' });

  useEffect(() => {
    if (!contact) return;
    load();
  }, [contact?.id]);

  async function load() {
    const [a, r] = await Promise.all([
      api.fetchActivities(contact.id),
      api.fetchReminders(contact.id)
    ]);
    setActivities(a);
    setReminders(r);
  }

  if (!contact) return null;

  async function submitActivity(e) {
    e.preventDefault();
    await api.addActivity(contact.id, {
      contact_id: contact.id,
      type: activityForm.type,
      subject: activityForm.subject,
      notes: activityForm.body,
      timestamp: new Date().toISOString()
    });
    setActivityForm({ type: 'note', subject: '', body: '' });
    await load();
    onRefresh();
  }

  async function submitReminder(e) {
    e.preventDefault();
    await api.createReminder({ contact_id: contact.id, title: reminderForm.title, due_date: reminderForm.dueAt, notes: reminderForm.notes });
    setReminderForm({ title: '', dueAt: '', notes: '' });
    await load();
    onRefresh();
  }

  async function completeReminder(id) {
    await api.completeReminder(id);
    await load();
    onRefresh();
  }

  return (
    <div className="fixed inset-0 z-40 bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="mx-auto grid max-h-[95vh] max-w-6xl gap-6 overflow-auto rounded-3xl border border-white/10 bg-slate-900/95 p-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div>
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-[0.3em] text-cyan-300">Contact Inspector</div>
               <h2 className="mt-2 text-3xl font-semibold text-white">{contact.name || 'Unnamed Contact'}</h2>
               <p className="mt-2 text-slate-400">{contact.metadata?.company || contact.metadata?.department || ''}</p>
            </div>
            <button onClick={onClose} className="rounded-xl border border-white/10 px-3 py-2 text-slate-300">Close</button>
          </div>

          <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="mb-4 text-xs uppercase tracking-[0.24em] text-slate-500">Activity Timeline</div>
            <form onSubmit={submitActivity} className="mb-6 grid gap-3">
              <div className="grid gap-3 md:grid-cols-3">
                <select className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" value={activityForm.type} onChange={(e) => setActivityForm({ ...activityForm, type: e.target.value })}>
                  <option value="note">Note</option>
                  <option value="call">Call</option>
                  <option value="email">Email</option>
                  <option value="meeting">Meeting</option>
                </select>
                <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white md:col-span-2" placeholder="Subject" value={activityForm.subject} onChange={(e) => setActivityForm({ ...activityForm, subject: e.target.value })} required />
              </div>
              <textarea className="min-h-24 rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Details" value={activityForm.body} onChange={(e) => setActivityForm({ ...activityForm, body: e.target.value })} />
              <button className="w-fit rounded-2xl border border-cyan-300/30 bg-cyan-400/20 px-5 py-3 text-cyan-100">Add Activity</button>
            </form>

            <div className="space-y-3">
              {activities.map(item => (
                <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                   <div className="flex flex-wrap items-center justify-between gap-2">
                     <div className="text-sm uppercase tracking-[0.22em] text-cyan-300">{item.type}</div>
                     <div className="text-xs text-slate-500">{item.created_at}</div>
                   </div>
                   <div className="mt-2 text-lg font-medium text-white">{item.subject}</div>
                   <div className="mt-2 text-sm text-slate-300">{item.notes || 'No extra detail.'}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="mb-4 text-xs uppercase tracking-[0.24em] text-slate-500">Reminders</div>
            <form onSubmit={submitReminder} className="mb-6 grid gap-3">
              <input className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Reminder title" value={reminderForm.title} onChange={(e) => setReminderForm({ ...reminderForm, title: e.target.value })} required />
              <input type="datetime-local" className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" value={reminderForm.dueAt} onChange={(e) => setReminderForm({ ...reminderForm, dueAt: e.target.value })} required />
              <textarea className="min-h-20 rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white" placeholder="Reminder notes" value={reminderForm.notes} onChange={(e) => setReminderForm({ ...reminderForm, notes: e.target.value })} />
              <button className="w-fit rounded-2xl border border-cyan-300/30 bg-cyan-400/20 px-5 py-3 text-cyan-100">Add Reminder</button>
            </form>

            <div className="space-y-3">
              {reminders.map(item => (
                <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                  <div className="flex items-center justify-between gap-3">
                     <div>
                       <div className="text-white">{item.title}</div>
                       <div className="mt-1 text-xs text-slate-500">{item.due_date}</div>
                     </div>
                     {!item.completed
                       ? <button onClick={() => completeReminder(item.id)} className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-100">Complete</button>
                       : <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200">Completed</span>}
                  </div>
                  <div className="mt-2 text-sm text-slate-300">{item.notes || 'No notes.'}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="mb-4 text-xs uppercase tracking-[0.24em] text-slate-500">Contact Snapshot</div>
             <pre className="overflow-auto rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-xs text-slate-300">{JSON.stringify(contact.metadata || {}, null, 2)}</pre>
          </section>
        </div>
      </div>
    </div>
  );
}
