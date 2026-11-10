#!/usr/bin/env python3
"""Verify copied small evidence and recompute headline statistics without raw inputs or VPR."""
from pathlib import Path
import json,csv,hashlib,math,statistics,collections,sys
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D/'source'))
from run_v4_timing_protocol import signature,feedback_signature
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def csvrows(p):return list(csv.DictReader(p.open()))
cohort=read(D/'evidence/history/cohort/summary.json');cases=cohort['cases'];assert len(cases)==13
passed=[c for c in cases if c['status']=='pass'];failed=[c for c in cases if c['status']=='fail'];assert len(passed)==9 and len(failed)==4
ids=set()
for c in passed:
 for i,rr in enumerate(c['repeats']):
  p=D/'evidence/history/cohort'/c['design']/f'run_{i:02}'/'report.json';assert sha(p)==rr['sha256'];r=read(p);ids.add(r['provenance']['implementation']['sha256']);assert r['final']==c['final'] or (r['final']['cpd_ns']==c['final']['cpd_ns'] and r['final']['wirelength']==c['final']['wirelength'] and r['final']['legal']==c['final']['legal'])
assert ids=={'2fa6e2324a971d8489bba12d49115f91d0a56874c0ee5200224d72e4f8a9f689'}
audit=read(D/'evidence/history/cohort/final_audit.json')
for case in audit['cases']:
 if case['status']=='fail':
  f=D/'evidence/history/preparation'/case['design']/('baseline/process.json' if case['failed_stage']=='baseline' else 'inputs/paths.process.json')
  assert sha(f)==case['process_sha256']
  assert read(f)['returncode']==case['process']['returncode']
tr=csvrows(D/'evidence/historical_trial_index.csv');assert len(tr)==404
for t in tr:
 f=D/t['evidence_path'];assert sha(f)==t['native_sha256'];r=read(f);assert str(r['wirelength'])==t['wl'] and float(r['cpd_ns'])==float(t['cpd_ns']) and str(r['legal'])==t['legal']
result={'historical_cases':13,'historical_successes':9,'historical_failures':[c['design'] for c in failed],'historical_native_trials':len(tr),'historical_implementation':list(ids),'historical_success_subset_geomean_change_pct':{k:100*(math.exp(statistics.mean(math.log(c['final'][k]/c['baseline'][k]) for c in passed))-1) for k in ['cpd_ns','wirelength']}}
summary=read(D/'evidence/pilot/summary.json');p=read(D/'PILOT_PROTOCOL.json');results=[]
assert sha(D/'PILOT_PROTOCOL.json')==summary['pre_run']['protocol_sha256']
for source in p['implementation']['sources']:assert sha(D/'source'/source['name'])==source['sha256']
expected_inputs={r['path']:r['sha256'] for r in p['files']}
for case in p['cases']:
 rr=[r for r in summary['runs'] if r['case']==case['case'] and r['kind']!='baseline_smoke' and r.get('status')=='completed'];A=[r for r in rr if r['arm']=='A'];B=[r for r in rr if r['arm']=='B'];eq='NOT_ESTABLISHED'
 if A and B:
  ref=read(D/'evidence/pilot'/A[0]['run_id']/'exact_signature.json');assert ref['decisions']['trials'];eq=all(read(D/'evidence/pilot'/r['run_id']/'exact_signature.json')==ref for r in B)
 for r in rr:
  folder=D/'evidence/pilot'/r['run_id'];report=read(folder/'report.json');timing=read(folder/'timing.json');assert report['provenance']['implementation']['sha256']==p['implementation']['sha256'];assert sha(folder/'report.json')==timing['report']['sha256']
  for v in report['provenance']['inputs']:assert expected_inputs.get(v['path'])==v['sha256']
  assert timing['pressure_prefix']==(r['arm']=='A')
  derived={'decisions':signature(report),'feedback':feedback_signature(report),'phases':report['phases'],'costs':[x['transactions'] for x in report['trials']],'native_legal':[x['closure']['legal'] for x in report['trials']]}
  assert derived==read(folder/'exact_signature.json')
  assert timing['search_other_wall_s']>=-1e-6 and r['outer_wall_s']-timing['flow_wall_s']>=-1e-6
  assert abs(timing['preparation_wall_s']+timing['search_wall_s']+timing['output_wall_s']-timing['flow_wall_s'])<1e-5
  assert abs(sum(timing['search_stage_wall_s'].values())+timing['search_other_wall_s']-timing['search_wall_s'])<1e-5
  for j,t in enumerate(report['trials']):assert sha(folder/f'native_{j:02}.json')==t['closure']['report_sha256']
 a=[r['outer_wall_s'] for r in A if r['kind']=='measured'];b=[r['outer_wall_s'] for r in B if r['kind']=='measured'];results.append({'case':case['case'],'measured_A_s':a,'measured_B_s':b,'median_B_over_A':statistics.median(b)/statistics.median(a) if a and b else 'not_established','cross_arm_exact':eq})
result['pilot']=results;result['status_counts']=dict(collections.Counter(r.get('status','not_started') for r in summary['runs']));result['observed_process_wall_sum_s']=sum(r.get('outer_wall_s',0) for r in summary['runs']);result['limits']='Verifies compact evidence consistency, not an independent native rerun. Raw routes, inputs, and binaries remain local.'
print(json.dumps(result,indent=2,sort_keys=True))
