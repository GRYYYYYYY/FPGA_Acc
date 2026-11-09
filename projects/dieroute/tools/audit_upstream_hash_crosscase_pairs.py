"""Review two complete development cohorts separately; no pooled FPGA claim."""
import argparse,hashlib,json,statistics
from pathlib import Path
from audit_upstream_hash_native_pairs import compare
R=Path(__file__).resolve().parents[1]
D=R/'work/upstream_hash_crosscase_pairs_20261018'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check-only',action='store_true');p.add_argument('--case',choices=['diffeq','alu4']);a=p.parse_args()
 m=json.loads((D/'manifest.json').read_text());protocol=json.loads((D/'protocol.json').read_text());cases=[a.case] if a.case else protocol['cases']
 selected=[s for s in m['steps'] if s['case'] in cases]
 ready=len(selected)==10*len(cases) and all(s.get('returncode') is not None for s in selected)
 if not a.case:ready=ready and m['status']=='twenty_crosscase_attempts_terminal_requires_independent_review'
 if a.check_only:print(json.dumps({'selected_cases':cases,'selected_attempts_terminal':ready,'review_started':False}));return
 assert ready and len(protocol['steps'])==20
 output=D/(f'independent_case_audit_{a.case}.json' if a.case else 'independent_pair_audit.json');assert not output.exists()
 refs={}
 def sha(p):
  p=Path(p);h=hashlib.sha256(p.read_bytes()).hexdigest();refs[str(p)]=h;return h
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 assert all(s.get('returncode')==0 for s in selected),'Failures remain in20attempt denominator; classify before equivalence/performance claims'
 summaries=[]
 for case in cases:
  reference=D/'runs'/f'{case}_pair0_parent';q=json.loads((reference/'route.json').read_text());epochs=q['iterations'];assert q['legal'];runs=[];pairs=[]
  for i in range(5):
   values={}
   for arm in ['parent','candidate']:
    label=f'{case}_pair{i}_{arm}';directory=D/'runs'/label;mp=directory/'manifest.json';run=json.loads(mp.read_text());assert run['status']=='online_router_completed_equivalence_audit_required' and run['returncode']==0 and run['requests']==epochs;sha(mp)
    checks=compare(reference,directory);assert sum(c['name'].endswith('.input.csv') for c in checks)==epochs and sum(c['name'].endswith('.output.csv') for c in checks)==epochs
    session=directory/'session_provenance_audit.json';s=json.loads(session.read_text());assert s['epochs']==epochs;sha(session)
    for f,h in s['source_sha256'].items():assert sha(f)==h,f
    step,=[s for s in m['steps'] if s['label']==label];ns=step['complete_process_wall_ns'];assert ns>=run['cold_start_through_shutdown_ns']>0;values[arm]=ns;runs.append({'label':label,'comparisons':checks,'complete_process_wall_ns':ns})
    if i==0:
     p=directory/'native_validation/validation.json';v=json.loads(p.read_text());assert all(v[k] for k in ['legal','route_loaded','routing_consistency','successfully_routed','vpr_succeeded']) and v['vpr_exit_status']==0;sha(p)
     cfg=json.loads((D/'recipes'/case/arm/'pair.json').read_text())['steps'][0]['routing_environment']
     inputs={'vpr':Path(v['command'][0]),'arch':Path(cfg['PERSISTROUTE_VPR_ARCH']),'circuit':Path(cfg['PERSISTROUTE_VPR_CIRCUIT']),'net':Path(cfg['PERSISTROUTE_VPR_NET']),'place':Path(cfg['PERSISTROUTE_VPR_PLACE']),'rr_graph':Path(cfg['PERSISTROUTE_VPR_RR_GRAPH']),'route':directory/'native.route'}
     for key,path in inputs.items():assert sha(path)==v['inputs'][key+'_sha256'],key
     for name,key in [('vpr_analysis.stdout','stdout_sha256'),('vpr_analysis.stderr','stderr_sha256')]:assert sha(directory/'native_validation'/name)==v[key]
   pairs.append({'pair':i,'parent_ns':values['parent'],'candidate_ns':values['candidate'],'candidate_change_percent':100*(values['candidate']/values['parent']-1),'parent_over_candidate':values['parent']/values['candidate']})
  summaries.append({'case':case,'cost_scale':256,'epochs':epochs,'runs':runs,'pairs':pairs,'median_candidate_change_percent':statistics.median(v['candidate_change_percent'] for v in pairs),'median_paired_ratio':statistics.median(v['parent_over_candidate'] for v in pairs)})
 snapshot=D/(f'case_{a.case}_terminal_steps.json' if a.case else 'all_terminal_steps.json')
 with snapshot.open('x') as f:json.dump({'steps':selected,'observed_cohort_status':m['status']},f,indent=2);f.write('\n')
 for f in [D/'protocol.json',snapshot,D/'launch_receipt.json',Path(__file__).resolve(),R/'tools/audit_upstream_hash_native_pairs.py']:sha(f)
 result={'status':('one_development_case_all10_outputs_sessions_and_matched_times_reviewed' if a.case else 'two_development_cases_all20_outputs_sessions_and_matched_times_reviewed'), 'reviewed_attempts':len(selected),'planned_attempts_total':20,'cases':summaries,'source_sha256':refs,'scope':'Selected original scale256 development configurations, five alternating-order pairs each, shared host and warm caches. Case-only review does not establish completion of the other case. First pair in each case native validated, later outputs identical. Cases reported separately; not representative heldout/general guarantee, FPGA performance or adoption.','adopted':False,'research_complete':False}
 with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
