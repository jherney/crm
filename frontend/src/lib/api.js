const API_BASE = '/api';

async function handle(response) {
  if (!response.ok) {
    let msg = 'Request failed';
    try {
      const data = await response.json();
      msg = data.error || msg;
    } catch {}
    throw new Error(msg);
  }
  const type = response.headers.get('content-type') || '';
  return type.includes('application/json') ? response.json() : response.text();
}

export const api = {
  fetchContacts(search = '', includeDeleted = false) {
    const qs = new URLSearchParams();
    if (search) qs.set('search', search);
    if (includeDeleted) qs.set('includeDeleted', 'true');
    return fetch(`${API_BASE}/contacts?${qs}`).then(handle);
  },
  createContact(payload) {
    return fetch(`${API_BASE}/contacts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handle);
  },
  updateContact(id, payload) {
    return fetch(`${API_BASE}/contacts/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handle);
  },
  deleteContact(id) { return fetch(`${API_BASE}/contacts/${id}`, { method: 'DELETE' }).then(handle); },
  restoreContact(id) { return fetch(`${API_BASE}/contacts/${id}/restore`, { method: 'POST' }).then(handle); },
  purgeContact(id) { return fetch(`${API_BASE}/contacts/${id}/purge`, { method: 'DELETE' }).then(handle); },
  fetchTags() { return fetch(`${API_BASE}/tags`).then(handle); },
  createTag(payload) {
    return fetch(`${API_BASE}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handle);
  },
  fetchActivities(contactId) { return fetch(`${API_BASE}/contacts/${contactId}/activities`).then(handle); },
  addActivity(contactId, payload) {
    return fetch(`${API_BASE}/contacts/${contactId}/activities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handle);
  },
  fetchReminders(contactId = '') {
    const qs = new URLSearchParams();
    if (contactId) qs.set('contactId', contactId);
    return fetch(`${API_BASE}/reminders?${qs}`).then(handle);
  },
  createReminder(payload) {
    return fetch(`${API_BASE}/reminders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handle);
  },
  completeReminder(id) {
    return fetch(`${API_BASE}/reminders/${id}/complete`, { method: 'POST' }).then(handle);
  },
  fetchAuditLogs(limit = 100) { return fetch(`${API_BASE}/audit-logs?limit=${limit}`).then(handle); },
  async exportCsv() {
    const response = await fetch(`${API_BASE}/contacts/export/csv`);
    if (!response.ok) throw new Error('Export failed');
    return response.text();
  },
  async importCsv(file) {
    const form = new FormData();
    form.append('file', file);
    const response = await fetch(`${API_BASE}/contacts/import/csv`, { method: 'POST', body: form });
    return handle(response);
  }
};
