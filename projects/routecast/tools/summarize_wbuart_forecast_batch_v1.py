"""All fixed label-free arms and complete audit/state availability; no quality scoring."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_forecasts_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 t=read(D/'terminal.json');m=read(D/'manifest.json');assert len(t['rows'])==9 and t['all_pass']
 for n,h in m['bindings'].items():assert sha(Path(n))==h
 bindings={str(p):sha(p) for p in [Path(__file__),D/'terminal.json',D/'manifest.json']};rows=[];events=0;arm_count=0
 for c in m['cases']:
  if c['reuse_preflight_arms']:arms=c['reuse_preflight_arms']
  else:
   vp=Path(c['output'])/'verification.json';v=read(vp);arms=v['arms'];assert all(p['round0_equal'] for p in v['parity']);bindings[str(vp)]=sha(vp)
  seen=set();case_arms=[]
  for arm in arms:
   policy=arm['timing_policy'] if 'timing_policy' in arm else arm['policy'];init=arm['initializer'];assert (init,policy) not in seen;seen.add((init,policy));out=Path(arm['output']);ap=out/'complete_event_audit.json';a=read(ap);assert all(a[k] for k in ['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass','complete_round_timing_original_XML_recurrence_component_assembly_and_setup_pass','complete_present_snapshot_owner_exclusion_and_union_objective_pass'])
   for n,h in a['bindings'].items():assert sha(Path(n))==h
   assert a['bindings'][c['endpoint']]==sha(Path(c['endpoint']));r=read(out/'receipt.json');state=read(out/'sketch.json');ep=read(Path(c['endpoint']));qs={q['connection_id']:q for q in ep['connections']};assert len(state['records'])==state['required_connections']==state['completed_connections']==2493 and state['graph_sha256']==ep['graph_sha256'];assert {q['connection_id'] for q in state['records']}==set(qs)
   assert all(q['full_connection_id']==qs[q['connection_id']]['full_connection_id'] for q in state['records']);assert len(r['rounds'])==2 and all(len(x['events'])==1074 for x in r['rounds']);count=sum(len(x['events']) for x in r['rounds']);events+=count;arm_count+=1;bindings[str(ap)]=sha(ap);case_arms.append({'initializer':init,'timing_policy':policy,'complete_NET_events':count,'final_overflow_units':state['overflow_units'],'output':str(out)})
  assert seen=={(i,p) for i in m['initializers'] for p in m['timing_policies']}
  for init in m['initializers']:
   a,b=[Path(r['output']) for r in case_arms if r['initializer']==init];ra,rb=read(a/'receipt.json'),read(b/'receipt.json');assert ra['rounds'][0]['events']==rb['rounds'][0]['events'];assert read(a/'round0.json')==read(b/'round0.json');assert read(a/'timing_round0.json')['criticalities']==read(b/'timing_round0.json')['criticalities']
  rows.append({'case':c['case'],'arms':case_arms})
 assert arm_count==36 and events==77328 and not list(D.rglob('*.route'))
 result={'status':'ALL9_FIXED_CASES_36_ARMS_77328_EVENTS_COMPLETE_AUDITS_AND_CID_PROVENANCE_VERIFIED','rows':rows,'arms':arm_count,'NET_events':events,'primary_policy':m['primary_timing_policy'],'native_target_label_availability':'not_generated','quality_gate_evaluated':False,'native_utility_evaluated':False,'matched_full_paid_time_evaluated':False,'strict_unseen_admitted':False,'scope':'Complete prospective forecasts and timing ablation only. Final overflow diagnostics are not quality/native feasibility/gain evidence. First four preflight arms reused with historical costs retained.','bindings':bindings};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('ALL9_36_FORECASTS_VERIFIED',events,flush=True)
if __name__=='__main__':main()
