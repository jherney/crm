async function apiCall(method, url, body) {
    const opts = {
        method,
        headers: {}
    };
    if (body !== undefined) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const resp = await fetch(url, opts);
    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `${resp.status} ${resp.statusText}`);
    }
    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('json')) {
        return resp.json();
    }
    return resp.text();
}

async function apiGet(url) {
    return apiCall('GET', url);
}

async function apiPost(url, body) {
    return apiCall('POST', url, body);
}

async function apiPut(url, body) {
    return apiCall('PUT', url, body);
}

async function apiDelete(url) {
    return apiCall('DELETE', url);
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function debounce(fn, ms) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), ms);
    };
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(/\s+/).filter(Boolean).map(w => w[0]).join('').substring(0, 2).toUpperCase() || '?';
}

function highlightCurrentNav() {
    const path = window.location.pathname;
    const filename = path.split('/').filter(Boolean)[0] || 'dashboard';
    document.querySelectorAll('.nav-link').forEach(link => {
        const linkPath = link.getAttribute('href').split('/').filter(Boolean)[0] || 'dashboard';
        if (linkPath === filename) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

async function loadModules() {
    const container = document.getElementById('module-list');
    if (!container) return;
    try {
        const modules = await apiGet('/api/modules');
        container.innerHTML = (modules || []).filter(m => m.enabled).map(m => `
            <div class="module-item">${escapeHtml(m.name)}</div>
        `).join('') || '<div class="empty">No modules</div>';
    } catch (e) {
        container.textContent = 'Failed to load modules';
    }
}

function initTheme() {
    const saved = localStorage.getItem('crm-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
}

document.addEventListener('DOMContentLoaded', () => {
    highlightCurrentNav();
    loadModules();
    initTheme();

    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('crm-theme', next);
        });
    }
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
}
