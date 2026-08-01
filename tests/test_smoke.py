import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = 'http://127.0.0.1:5001'
PASS, FAIL = 0, 0


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f'  \u2713 {name}')
    except AssertionError as e:
        FAIL += 1
        print(f'  \u2717 {name}: {e}')
    except Exception as e:
        FAIL += 1
        print(f'  \u2717 {name}: {type(e).__name__}: {e}')


def request(method, path, body=None, expect=200):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={'Content-Type': 'application/json'} if data is not None else {},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == expect, f'expected {expect}, got {resp.status}'
        ct = resp.headers.get('content-type', '')
        return json.loads(resp.read().decode()) if 'json' in ct else resp.read()


def wait_for_server():
    for i in range(30):
        try:
            urllib.request.urlopen(BASE + '/api/health', timeout=1)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('server did not start')


def main():
    global PASS, FAIL
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    print('Starting CRM server from', root)
    proc = subprocess.Popen(
        [sys.executable, 'run.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for_server()
        print('Running tests...')

        test('health endpoint', lambda: request('GET', '/api/health'))
        test('modules endpoint', lambda: request('GET', '/api/modules'))
        test('dashboard stats', lambda: request('GET', '/dashboard/api/stats'))

        company = request('POST', '/companies/api/companies', {
            'name': 'Acme Corp',
            'industry': 'Technology',
            'status': 'customer',
        }, expect=201)
        assert company['id'], 'company created with id'
        print(f'  \u2713 create company (id={company["id"][:8]}...)')
        PASS += 1

        companies = request('GET', '/companies/api/companies')
        assert any(c['id'] == company['id'] for c in companies)
        print(f'  \u2713 list companies')
        PASS += 1

        contact = request('POST', '/contacts/api/contacts', {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice@example.com',
            'status': 'lead',
            'company_id': company['id'],
        }, expect=201)
        assert contact['id'], 'contact created with id'
        assert contact['company']['name'] == 'Acme Corp'
        print(f'  \u2713 create contact (id={contact["id"][:8]}...)')
        PASS += 1

        contacts = request('GET', '/contacts/api/contacts')
        assert any(c['id'] == contact['id'] for c in contacts)
        print(f'  \u2713 list contacts')
        PASS += 1

        fetched = request('GET', f'/contacts/api/contacts/{contact["id"]}')
        assert fetched['email'] == 'alice@example.com'
        print(f'  \u2713 get contact')
        PASS += 1

        request('PUT', f'/contacts/api/contacts/{contact["id"]}', {
            'first_name': 'Alice',
            'last_name': 'Anderson',
        })
        updated = request('GET', f'/contacts/api/contacts/{contact["id"]}')
        assert updated['full_name'] == 'Alice Anderson'
        print(f'  \u2713 update contact')
        PASS += 1

        request('DELETE', f'/contacts/api/contacts/{contact["id"]}')
        request('DELETE', f'/companies/api/companies/{company["id"]}')
        print(f'  \u2713 delete contact and company')
        PASS += 1

        # ---------- Deals / Pipeline module ----------

        stages = request('GET', '/deals/api/stages')
        assert isinstance(stages, list) and len(stages) == 6
        assert any(s['key'] == 'closed_won' and s['is_won'] for s in stages)
        print(f'  \u2713 list deal stages ({len(stages)} stages)')
        PASS += 1

        deal = request('POST', '/deals/api/deals', {
            'name': 'Acme Annual License',
            'value': 50000,
            'currency': 'USD',
            'stage': 'qualified',
            'company_id': '',  # re-link later
            'source': 'Referral',
        }, expect=201)
        # Note: company was just deleted; we'll use a fresh one for tests below.
        deal_id = deal['id']
        assert deal['probability'] == 25  # qualified stage probability
        assert deal['weighted_value'] == 12500
        print(f'  \u2713 create deal (id={deal_id[:8]}..., weighted={deal["weighted_value"]})')
        PASS += 1

        # Link to a fresh contact+company
        c2 = request('POST', '/companies/api/companies', {'name': 'Globex Inc', 'status': 'prospect'}, expect=201)
        ct2 = request('POST', '/contacts/api/contacts', {
            'first_name': 'Bob', 'last_name': 'Lee', 'email': 'bob@globex.com',
            'company_id': c2['id'],
        }, expect=201)
        request('PUT', f'/deals/api/deals/{deal_id}', {
            'company_id': c2['id'],
            'contact_id': ct2['id'],
        })
        fetched = request('GET', f'/deals/api/deals/{deal_id}')
        assert fetched['company']['name'] == 'Globex Inc'
        assert fetched['contact']['full_name'] == 'Bob Lee'
        print(f'  \u2713 deal links to company + contact')
        PASS += 1

        # Move between stages via /move (drag-and-drop)
        moved = request('POST', f'/deals/api/deals/{deal_id}/move', {'stage': 'proposal'})
        assert moved['stage'] == 'proposal'
        assert moved['probability'] == 50  # proposal probability auto-applied
        print(f'  \u2713 move deal to proposal stage (probability set to {moved["probability"]})')
        PASS += 1

        # Move to closed_won, expect closed_at auto-filled
        won = request('POST', f'/deals/api/deals/{deal_id}/move', {'stage': 'closed_won'})
        assert won['is_won'] is True
        assert won['closed_at'] is not None
        print(f'  \u2713 move deal to closed_won (closed_at={won["closed_at"]})')
        PASS += 1

        # Pipeline endpoint groups deals
        pipeline = request('GET', '/deals/api/pipeline')
        assert 'stages' in pipeline and 'deals_by_stage' in pipeline
        assert 'totals_by_stage' in pipeline
        print(f'  \u2713 pipeline endpoint returns stages + grouping + totals')
        PASS += 1

        # Stats endpoint
        stats = request('GET', '/deals/api/stats')
        assert stats['won'] >= 1
        assert stats['won_value'] >= 50000
        print(f'  \u2713 deals stats (won={stats["won"]}, won_value={stats["won_value"]})')
        PASS += 1

        # Create another deal and bucket-search by stage/probability
        d2 = request('POST', '/deals/api/deals', {
            'name': 'Pilot Project', 'value': 10000, 'stage': 'negotiation',
        }, expect=201)
        filtered = request('GET', '/deals/api/deals?stage=negotiation')
        assert any(d['id'] == d2['id'] for d in filtered)
        print(f'  \u2713 stage filter works')
        PASS += 1

        # Cleanup test deals + contact + company
        request('DELETE', f'/deals/api/deals/{deal_id}')
        request('DELETE', f'/deals/api/deals/{d2["id"]}')
        request('DELETE', f'/contacts/api/contacts/{ct2["id"]}')
        request('DELETE', f'/companies/api/companies/{c2["id"]}')
        print(f'  \u2713 delete deals + linked records')
        PASS += 1

        # ---------- Activities module ----------

        types_list = request('GET', '/activities/api/types')
        assert 'call' in types_list and 'email' in types_list
        print(f'  \u2713 activities types list ({len(types_list)} types)')
        PASS += 1

        # Create a fresh contact+deal for activities
        comp = request('POST', '/companies/api/companies', {'name': 'Initech', 'status': 'prospect'}, expect=201)
        cont = request('POST', '/contacts/api/contacts', {
            'first_name': 'Peter', 'last_name': 'Gibbons',
            'email': 'peter@initech.com', 'company_id': comp['id'],
        }, expect=201)
        d3 = request('POST', '/deals/api/deals', {
            'name': 'TPS Reporting Suite', 'value': 22000, 'stage': 'qualified',
            'contact_id': cont['id'], 'company_id': comp['id'],
        }, expect=201)
        d3_id = d3['id']
        print(f'  \u2713 setup deal+contact+company for activities')
        PASS += 1

        from datetime import datetime, timedelta, timezone
        soon = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

        a1 = request('POST', '/activities/api/activities', {
            'type': 'call', 'subject': 'Discovery call with Peter',
            'deal_id': d3_id, 'contact_id': cont['id'],
            'due_date': soon,
        }, expect=201)
        assert a1['type'] == 'call' and a1['subject'] == 'Discovery call with Peter'
        print(f'  \u2713 create activity (open call)')
        PASS += 1

        a_overdue = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        a2 = request('POST', '/activities/api/activities', {
            'type': 'task', 'subject': 'Send proposal draft',
            'deal_id': d3_id, 'due_date': a_overdue,
        }, expect=201)
        assert a2['is_overdue'] is True
        print(f'  \u2713 overdue auto-detected')
        PASS += 1

        complete = request('POST', f'/activities/api/activities/{a1["id"]}/complete', {})
        assert complete['completed'] is True
        assert complete['completed_at'] is not None
        print(f'  \u2713 mark activity complete via /complete endpoint')
        PASS += 1

        upcoming = request('GET', '/activities/api/upcoming?limit=5')
        assert isinstance(upcoming, list)
        # Mark a2 complete too
        request('POST', f'/activities/api/activities/{a2["id"]}/complete', {})

        activities_by_deal = request('GET', f'/activities/api/activities?deal_id={d3_id}')
        assert len(activities_by_deal) >= 2
        print(f'  \u2713 filter activities by deal_id ({len(activities_by_deal)} activities on deal)')
        PASS += 1

        # ---------- Email Templates module ----------

        fields = request('GET', '/email-templates/api/merge-fields')
        assert 'contact.first_name' in fields and 'deal.name' in fields
        print(f'  \u2713 list merge fields ({len(fields)} fields)')
        PASS += 1

        tpl = request('POST', '/email-templates/api/templates', {
            'name': 'Welcome to {{deal.name}}',
            'subject': 'Hi {{contact.first_name}}, your {{deal.name}} is in motion',
            'body': 'Hey {{contact.first_name}},\n\nExcited to be working on {{deal.name}} for {{company.name}}.\n\n- Alex',
            'category': 'follow-up',
        }, expect=201)
        assert tpl['id']
        print(f'  \u2713 create email template with merge fields')
        PASS += 1

        preview = request('POST', f'/email-templates/api/templates/{tpl["id"]}/preview', {
            'contact': {'first_name': 'Peter'},
            'deal': {'name': 'TPS Reporting Suite'},
            'company': {'name': 'Initech'},
            'user': {'name': 'Alex', 'email': 'alex@example.com'},
        })
        assert 'Peter' in preview['subject']
        assert 'TPS Reporting Suite' in preview['body']
        assert '{{contact.first_name}}' not in preview['subject']  # merged
        print(f'  \u2713 merge fields render correctly')
        PASS += 1

        # "Send" the template (logs an email activity)
        send = request('POST', f'/email-templates/api/templates/{tpl["id"]}/use', {
            'contact_id': cont['id'], 'deal_id': d3_id, 'company_id': comp['id'],
            'user_name': 'Alex', 'user_email': 'alex@example.com',
        }, expect=201)
        assert send['activity_id']
        # Now there should be an email activity tied to the deal
        acts_after_send = request('GET', f'/activities/api/activities?deal_id={d3_id}&type=email')
        assert any(a['id'] == send['activity_id'] for a in acts_after_send)
        print(f'  \u2713 sending template creates an email activity')
        PASS += 1

        # ---------- Automations module ----------

        triggers = request('GET', '/automations/api/triggers')
        assert any(t['key'] == 'deal_stage_changed' for t in triggers)
        print(f'  \u2713 list automations triggers ({len(triggers)} triggers)')
        PASS += 1

        rule = request('POST', '/automations/api/rules', {
            'name': 'Auto follow-up on negotiation',
            'description': 'When a deal enters negotiation, queue a follow-up call',
            'trigger': 'deal_stage_changed',
            'conditions': [{'field': 'deal.new_stage', 'op': 'equals', 'value': 'negotiation'}],
            'actions': [
                {'type': 'create_activity', 'activity_type': 'call',
                 'subject': 'Follow-up call after negotiation', 'due_in_days': 1,
                 'body': 'Auto-generated by automation.'}
            ],
        }, expect=201)
        rule_id = rule['id']
        print(f'  \u2713 create automation rule')
        PASS += 1

        # Trigger the rule by moving the test deal to negotiation
        request('POST', f'/deals/api/deals/{d3_id}/move', {'stage': 'proposal'})
        request('POST', f'/deals/api/deals/{d3_id}/move', {'stage': 'negotiation'})

        runs = request('GET', '/automations/api/runs?limit=20')
        triggered = [r for r in runs if r['rule_id'] == rule_id and r['status'] == 'success']
        assert triggered, f'expected rule to fire; got {len(runs)} runs'
        print(f'  \u2713 automation fired automatically on stage change ({len(triggered)} success run)')
        PASS += 1

        # Verify the rule created an activity on the deal
        post_deal = request('GET', f'/activities/api/activities?deal_id={d3_id}&type=call')
        assert any('Follow-up' in a['subject'] for a in post_deal)
        print(f'  \u2713 automation action created an activity on the deal')
        PASS += 1

        # ---------- Dashboard charts endpoints ----------

        forecast = request('GET', '/dashboard/api/forecast')
        assert 'pipeline_by_stage' in forecast and 'monthly' in forecast
        print(f'  \u2713 dashboard forecast endpoint')
        PASS += 1

        winrate = request('GET', '/dashboard/api/winrate')
        assert isinstance(winrate, list) and len(winrate) == 6
        print(f'  \u2713 win-rate endpoint ({len(winrate)} months)')
        PASS += 1

        by_type = request('GET', '/dashboard/api/activity-by-type')
        assert isinstance(by_type, list)
        print(f'  \u2713 activity-by-type endpoint ({len(by_type)} types)')
        PASS += 1

        # ---------- Cleanup ----------

        for a in request('GET', f'/activities/api/activities?deal_id={d3_id}'):
            request('DELETE', f'/activities/api/activities/{a["id"]}')
        request('DELETE', f'/deals/api/deals/{d3_id}')
        request('DELETE', f'/automations/api/rules/{rule_id}')
        request('DELETE', f'/email-templates/api/templates/{tpl["id"]}')
        request('DELETE', f'/contacts/api/contacts/{cont["id"]}')
        request('DELETE', f'/companies/api/companies/{comp["id"]}')
        print(f'  \u2713 cleanup')
        PASS += 1

        print(f'\nResults: {PASS} passed, {FAIL} failed')
        if FAIL:
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == '__main__':
    main()
