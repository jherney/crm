import { useEffect, useMemo, useState } from 'react';
import { api } from './lib/api';
import Sidebar from './components/Sidebar';
import Toolbar from './components/Toolbar';
import ContactCard from './components/ContactCard';
import ContactFormModal from './components/ContactFormModal';
import InspectorPanel from './components/InspectorPanel';
import TagManager from './components/TagManager';
import AuditLogPanel from './components/AuditLogPanel';

export default function App() {
  const [contacts, setContacts] = useState([]);
  const [tags, setTags] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [search, setSearch] = useState('');
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [inspectingContact, setInspectingContact] = useState(null);

  async function loadAll() {
    try {
      setLoading(true);
      const [contactsData, tagsData, remindersData, logsData] = await Promise.all([
        api.fetchContacts(search, includeDeleted),
        api.fetchTags(),
        api.fetchReminders(),
        api.fetchAuditLogs(40)
      ]);
      setContacts(contactsData.contacts || []);
      setTags(tagsData.tags || []);
      setReminders(remindersData.reminders || []);
      setAuditLogs(logsData.logs || []);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, [search, includeDeleted]);

  const deletedCount = useMemo(() => contacts.filter(c => c.deletedAt).length, [contacts]);

  async function handleSubmit(formData) {
    const payload = {
      firstName: formData.firstName,
      lastName: formData.lastName,
      email: formData.email,
      phone: formData.phone || null,
      company: formData.company,
      notes: formData.notes,
      favorite: formData.favorite,
      role: 'member',
      tags: formData.tagIds || [],
      customFields: formData.customFields || {},
      metadata: {},
      attachments: []
    };
    if (editingContact) await api.updateContact(editingContact.id, payload);
    else await api.createContact(payload);
    setModalOpen(false);
    setEditingContact(null);
    await loadAll();
  }

  async function handleDelete(id) {
    if (!window.confirm('Soft delete this contact?')) return;
    await api.deleteContact(id);
    await loadAll();
  }

  async function handleRestore(id) {
    await api.restoreContact(id);
    await loadAll();
  }

  async function handlePurge(id) {
    if (!window.confirm('Permanently delete this contact?')) return;
    await api.purgeContact(id);
    if (inspectingContact?.id === id) setInspectingContact(null);
    await loadAll();
  }

  async function handleExport() {
    const csv = await api.exportCsv();
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'contacts-export.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleImport(file) {
    if (!file) return;
    await api.importCsv(file);
    await loadAll();
  }

  async function handleCreateTag(tag) {
    await api.createTag(tag);
    await loadAll();
  }

  return (
    <div className="min-h-screen p-6 text-slate-100 lg:p-8">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[320px_1fr]">
        <Sidebar contacts={contacts.filter(c => !c.deletedAt)} reminders={reminders} deletedCount={deletedCount} />

        <main className="space-y-6">
          <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <div>
              <div className="text-xs uppercase tracking-[0.3em] text-cyan-300">Command Surface</div>
              <h2 className="mt-3 text-4xl font-semibold text-white">Upgraded Contact Management Console</h2>
              <p className="mt-3 max-w-3xl text-slate-400">
                SQLite-backed contact platform with FTS search, reminders, activities, tags, soft delete, audit history, custom fields, and CSV workflows.
              </p>
            </div>
          </section>

          <Toolbar
            search={search}
            setSearch={setSearch}
            includeDeleted={includeDeleted}
            setIncludeDeleted={setIncludeDeleted}
            onCreate={() => { setEditingContact(null); setModalOpen(true); }}
            onExport={handleExport}
            onImport={handleImport}
          />

          <TagManager tags={tags} onCreateTag={handleCreateTag} />

          {error && <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-rose-100">{error}</div>}

          {loading ? (
            <div className="rounded-3xl border border-white/10 bg-slate-900/40 p-8 text-slate-400 backdrop-blur-xl">Loading contact signals...</div>
          ) : (
            <section className="grid gap-5 lg:grid-cols-2">
              {contacts.map(contact => (
                <ContactCard
                  key={contact.id}
                  contact={contact}
                  onEdit={(c) => { setEditingContact(c); setModalOpen(true); }}
                  onDelete={handleDelete}
                  onRestore={handleRestore}
                  onPurge={handlePurge}
                  onInspect={setInspectingContact}
                />
              ))}
            </section>
          )}

          <AuditLogPanel logs={auditLogs} />
        </main>
      </div>

      <ContactFormModal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingContact(null); }}
        onSubmit={handleSubmit}
        initialData={editingContact}
        tags={tags}
      />

      <InspectorPanel contact={inspectingContact} onClose={() => setInspectingContact(null)} onRefresh={loadAll} />
    </div>
  );
}
