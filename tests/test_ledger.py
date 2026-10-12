import concurrent.futures
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'plugins/pmu-swarm/skills/pmu-swarm/scripts/pmu_state.py'

class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / 'run' / 'state.sqlite'
        self.brief = dict(goal='A verified result', intent='Support a decision', inputs=[], sources={'web': False}, constraints=[], acceptance=['Correct result'], assumptions=[])
        self.call('init', '--call-limit', '20', data=self.brief)

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, *args, data=None, ok=True):
        p = subprocess.run([sys.executable, str(SCRIPT), '--db', str(self.db), *args], input=json.dumps(data) if data is not None else None, text=True, capture_output=True)
        self.assertEqual(p.returncode, 0 if ok else 1, p.stdout + p.stderr)
        return json.loads(p.stdout if ok else p.stderr)

    def add(self, name='work', kind='work', deps=None, attempts=3, required=True):
        return self.call('add', data=dict(id=name, pmu='A', role='Analyst', title=name, acceptance=['Correct'], kind=kind, dependencies=deps or [], max_attempts=attempts, required=required))

    def claim(self, name='work', worker='author'):
        return self.call('claim', name, '--worker', worker)

    def submit(self, name, worker, claim, text='result'):
        path = Path(claim['scope']) / 'result.md'
        path.write_text(text)
        return self.call('submit', name, '--worker', worker, '--token', claim['token'], '--artifact', str(path))

    def draft(self):
        self.add()
        return self.submit('work', 'author', self.claim())

    def report(self, name='check', worker='reviewer'):
        self.add(name, 'review', ['work'])
        result = self.submit(name, worker, self.claim(name, worker), 'Verified independently')
        self.review(name, 'director', None)
        return result

    def review(self, name='work', reviewer='reviewer', report='check', decision='accept', ok=True, unresolved=None):
        args = ['review', name, '--reviewer', reviewer, '--decision', decision]
        if report: args += ['--report', report]
        return self.call(*args, data={'note':'Verified', 'unresolved':unresolved or []}, ok=ok)

    def test_full_lifecycle(self):
        self.draft(); self.report(); self.review()
        result = self.call('complete', data={'passed':True, 'note':'All checks pass', 'unresolved':[]})
        self.assertEqual(result['state'], 'completed')
        self.call('resume', ok=False)

    def test_racing_claims_reserve_one_call(self):
        self.add()
        def run(i):
            return subprocess.run([sys.executable,str(SCRIPT),'--db',str(self.db),'claim','work','--worker','w'+str(i)],capture_output=True,text=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(run,range(8)))
        self.assertEqual(sum(r.returncode == 0 for r in results), 1)
        self.assertEqual(self.call('status')['run']['calls'],1)

    def test_dependencies_and_review_ready_before_acceptance(self):
        self.add(); self.add('dependent',deps=['work']); self.add('check','review',['work'])
        self.call('claim','dependent','--worker','b',ok=False)
        self.call('claim','check','--worker','r',ok=False)
        self.submit('work','author',self.claim())
        self.claim('check','r')
        self.call('claim','dependent','--worker','b',ok=False)

    def test_late_worker_cannot_submit_after_reclaim(self):
        self.add(); old=self.claim()
        with sqlite3.connect(self.db) as c: c.execute("UPDATE tasks SET lease=0 WHERE id='work'")
        new=self.claim(worker='replacement')
        p=Path(old['scope'])/'old.md'; p.write_text('late')
        self.call('submit','work','--worker','author','--token',old['token'],'--artifact',str(p),ok=False)
        self.submit('work','replacement',new)

    def test_pause_invalidates_tokens_and_preserves_calls(self):
        self.add(); old=self.claim(); self.call('pause')
        self.call('heartbeat','work','--worker','author','--token',old['token'],ok=False)
        self.call('resume'); new=self.claim()
        self.assertNotEqual(old['token'],new['token'])
        self.assertEqual(self.call('status')['run']['calls'],2)

    def test_budget_ceiling(self):
        with sqlite3.connect(self.db) as c: c.execute('UPDATE run SET call_limit=1')
        self.add(); self.add('other'); self.claim()
        self.call('claim','other','--worker','b',ok=False)
        self.assertEqual(self.call('status')['run']['calls'],1)

    def test_attempt_ceiling(self):
        self.add(attempts=1); c=self.claim()
        self.call('fail','work','--worker','author','--token',c['token'],'--reason','Tool failure')
        self.assertEqual(self.call('status')['tasks'][0]['state'],'blocked')
        self.call('claim','work','--worker','b',ok=False)

    def test_author_and_stale_report_rejected(self):
        self.draft()
        self.add('selfcheck','review',['work'],required=False)
        self.call('claim','selfcheck','--worker','author',ok=False)
        self.report(); self.review(decision='revise')
        self.submit('work','author',self.claim(),text='changed')
        self.review(ok=False)
        self.review(reviewer='author',ok=False)

    def test_snapshot_and_hash_verification(self):
        submitted=self.draft()
        (self.db.parent/'tasks/work/result.md').write_text('new working copy')
        self.assertEqual(Path(submitted['artifact']).read_text(),'result')
        self.report()
        Path(submitted['artifact']).write_text('tampered')
        self.review(ok=False)

    def test_scope_and_empty_artifacts_rejected(self):
        self.add(); c=self.claim(); outside=self.root/'outside.md'; outside.write_text('wrong scope')
        self.call('submit','work','--worker','author','--token',c['token'],'--artifact',str(outside),ok=False)
        empty=Path(c['scope'])/'empty.md'; empty.write_text('')
        self.call('submit','work','--worker','author','--token',c['token'],'--artifact',str(empty),ok=False)

    def test_critical_findings_block_acceptance(self):
        self.draft(); self.report()
        self.review(ok=False,unresolved=[{'severity':'critical','description':'Wrong result'}])
        self.assertEqual(self.call('status')['tasks'][0]['state'],'submitted')

    def test_completion_and_cancellation_guards(self):
        self.add()
        self.call('complete',data={'passed':True,'note':'done','unresolved':[]},ok=False)
        self.call('cancel'); self.call('claim','work','--worker','a',ok=False)
        self.call('resume',ok=False)

    def test_mandate_tamper_and_audit_guards(self):
        with sqlite3.connect(self.db) as c:
            with self.assertRaises(sqlite3.IntegrityError): c.execute('DELETE FROM events')
        (self.db.parent/'brief.json').write_text('{}')
        self.call('status',ok=False)

    def test_final_expiry_is_persisted(self):
        self.add(attempts=1); self.claim()
        with sqlite3.connect(self.db) as c: c.execute("UPDATE tasks SET lease=0 WHERE id='work'")
        self.call('claim','work','--worker','b',ok=False)
        self.assertEqual(self.call('status')['tasks'][0]['state'],'blocked')

    def test_unaccepted_review_cannot_authorize_work(self):
        self.draft(); self.add('check','review',['work'],required=False)
        self.submit('check','reviewer',self.claim('check','reviewer'))
        self.review(ok=False)
        self.review('check','director',None,decision='reject')
        self.review(ok=False)

    def test_optional_report_hash_checked_at_completion(self):
        self.draft(); self.add('check','review',['work'],required=False)
        report=self.submit('check','reviewer',self.claim('check','reviewer'))
        self.review('check','director',None); self.review()
        Path(report['artifact']).write_text('changed')
        self.call('complete',data={'passed':True,'note':'done','unresolved':[]},ok=False)

    def test_accepted_review_checks_optional_input_snapshot(self):
        self.add(required=False)
        draft=self.submit('work','author',self.claim())
        self.report()
        Path(draft['artifact']).write_text('tampered optional input')
        self.call('complete',data={'passed':True,'note':'done','unresolved':[]},ok=False)

    def test_invalid_dependencies_and_ids(self):
        self.call('add',data=dict(id='../escape',pmu='A',role='a',title='a',acceptance=['a']),ok=False)
        self.call('add',data=dict(id='a',pmu='A',role='a',title='a',acceptance=['a'],dependencies=['missing']),ok=False)

if __name__ == '__main__': unittest.main()
