"""
Smoke test for the Modular CRM.

Runs standalone (also via `./runner.sh test`). Boots the app against a
throwaway SQLite database and exercises the core endpoints plus a CRUD
round-trip, including the events module.
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

# Make project-root imports work when run as `python3 tests/test_smoke.py`.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Must be set before importing the app so config picks up the temp DB.
_tmpdir = tempfile.mkdtemp(prefix='crm-smoke-')
os.environ['CRM_DATABASE_URL'] = f'sqlite:///{_tmpdir}/smoke.db'
os.environ['CRM_DEBUG'] = '0'

from app import create_app  # noqa: E402

FAILED = []


def check(name, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    print(f'  [{status}] {name}' + (f' — {detail}' if detail and not condition else ''))
    if not condition:
        FAILED.append(name)


def main():
    app = create_app()
    client = app.test_client()

    print('== Core ==')
    r = client.get('/api/health')
    check('GET /api/health', r.status_code == 200, str(r.get_data(as_text=True)))
    check('health reports db connected', r.get_json().get('db') == 'connected')

    r = client.get('/api/modules')
    slugs = {m['slug'] for m in r.get_json()}
    check('GET /api/modules', r.status_code == 200)
    expected = {'core', 'dashboard', 'contacts', 'companies', 'deals',
                'activities', 'email_templates', 'automations', 'events'}
    check('all modules registered', expected <= slugs, f'got {sorted(slugs)}')

    r = client.get('/')
    check('GET / (homepage)', r.status_code == 200)

    print('== Module endpoints ==')
    for url in ('/dashboard/api/stats', '/deals/api/deals', '/deals/api/stats',
                '/contacts/api/contacts', '/companies/api/companies',
                '/activities/api/activities', '/activities/api/stats',
                '/email-templates/api/templates', '/events/api/events',
                '/events/api/stats', '/events/api/statuses'):
        r = client.get(url)
        check(f'GET {url}', r.status_code == 200, f'{r.status_code}: {r.get_data(as_text=True)[:200]}')

    print('== CRUD round-trips ==')

    # Contact
    r = client.post('/contacts/api/contacts', json={
        'first_name': 'Smoke', 'last_name': 'Test', 'email': 'smoke@test.dev',
    })
    check('POST contact', r.status_code == 201, str(r.get_json()))
    contact_id = r.get_json()['id']
    check('GET contact', client.get(f'/contacts/api/contacts/{contact_id}').status_code == 200)
    check('DELETE contact', client.delete(f'/contacts/api/contacts/{contact_id}').status_code == 200)

    # Event + RSVP (new module)
    r = client.post('/events/api/events', json={
        'title': 'Smoke Test Event', 'date': '2099-06-01T10:00:00',
        'capacity': 1, 'status': 'published',
    })
    check('POST event', r.status_code == 201, str(r.get_json()))
    event_id = r.get_json()['id']

    r = client.post(f'/events/api/events/{event_id}/rsvps', json={'user_id': 'guest@example.com'})
    check('POST rsvp (attending)', r.status_code == 201 and r.get_json()['status'] == 'attending')

    r = client.post(f'/events/api/events/{event_id}/rsvps', json={'user_id': 'late@example.com'})
    check('rsvp auto-waitlists when full', r.get_json().get('status') == 'waitlist', str(r.get_json()))

    r = client.post('/events/api/events', json={'title': '', })
    check('POST event without title -> 400', r.status_code == 400)

    check('DELETE event cascades rsvps', client.delete(f'/events/api/events/{event_id}').status_code == 200)
    check('event gone', client.get(f'/events/api/events/{event_id}').status_code == 404)

    print()
    if FAILED:
        print(f'{len(FAILED)} check(s) FAILED:')
        for name in FAILED:
            print(f'  - {name}')
        return 1
    print('All smoke checks passed.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
