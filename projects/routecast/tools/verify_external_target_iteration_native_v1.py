"""All fixed cold/seed native pairs: full coverage, canonical and QoR comparison."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_native_target_iteration_observer_v1_2026-10-19';OLD=E/'prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def route_nodes(path):
 nets={};current=None
 for line in path.open():
  x=line.split()
  if x and x[0]=='Net':current=int(x[1]);assert current not in nets;nets[current]=set()
  elif x and x[0]=='Node:':assert current is not None;nets[current].add(int(x[1]))
 return nets

def main():
 terminal=read(D/'terminal.json');assert len(terminal['rows'])==6;manifest=read(D/'manifest.json');assert all(sha(p)==h for p,h in manifest['bindings'].items());lookup={c['case']:c for c in manifest['cases']};rows=[];bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'manifest.json'):sha(D/'manifest.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)};cases={}
 for r in terminal['rows']:
  key=r['case']+'/'+r['arm'];c=lookup[key];folder=Path(c['output']);vp=folder/'verification.json';a=read(vp);assert all(sha(p)==h for p,h in a['bindings'].items());assert r['status']==a['status'];passed=a['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';result=dict(case=r['case'],arm=r['arm'],native_physical_canonical_pass=passed,component_seconds=r['native_component_plus_audit_wall_seconds'],error=a.get('error'));bindings[str(vp)]=sha(vp)
  if passed:
   assert a['exit_status']==0 and a['canonical']['semantic_consistency_gate_pass'];ep=read(c['endpoint']);physical=read(folder/'physical_audit.json');text=(folder/'native.log').read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;assert physical['overflow_units']==0;assert Counter((q['net_id'],q['source'],q['sink']) for q in physical['connections'])==Counter((q['net_id'],q['source'],q['sink']) for q in ep['connections']);assert len(physical['connections'])==15616;unions=route_nodes(folder/'output.route');assert dict(Counter(n for ns in unions.values() for n in ns))=={int(n):v for n,v in physical['node_occupancy'].items()};assert (r['wirelength'],r['diagnostic_cpd_ns'],r['iterations'])==(a['wirelength'],a['diagnostic_cpd_ns'],a['iterations']);seeded='seed' in c['inputs'];assert seeded==(r['arm']=='seed');assert ('ROUTECAST NET-aware seed imported feasible=' in text)==seeded
   for k,name in [('blif','design.blif'),('net','design.net'),('place','design.place')]:assert sha(c['inputs'][k])==sha(folder/name)
   if seeded:assert sha(c['inputs']['seed'])==sha(folder/'seed.route')
   result.update(required_connections=15616,wirelength=a['wirelength'],diagnostic_cpd_ns=a['diagnostic_cpd_ns'],iterations=a['iterations'],seed_import_logged=seeded)
   if not seeded:result['cold_reproduces_archived_native_node_unions']=unions==route_nodes(OLD/'native'/r['case']/'output.route')
   for p in [folder/'output.route',folder/'physical_audit.json',folder/'native.log']:bindings[str(p)]=sha(p)
  cases[key]=result
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';cold,seed=cases[case+'/cold'],cases[case+'/seed'];both=cold['native_physical_canonical_pass'] and seed['native_physical_canonical_pass'];cpd=both and seed['diagnostic_cpd_ns']<=cold['diagnostic_cpd_ns'];wire=both and seed['wirelength']<=cold['wirelength'];rows.append(dict(case=case,cold=cold,seed=seed,CPD_nonregress=cpd,wirelength_nonregress=wire,full_coverage_and_QoR_pair_pass=both and cpd and wire))
 handoff_rows=[]
 for i in (1,2,3):
  import csv,math
  case=f'w160/episode_{i:02d}';f=D/case/'seed/native/first_delay_handoff.tsv';items=list(csv.DictReader(f.open(),delimiter='\t'));identities=[(int(r['net']),int(r['pin'])) for r in items];assert len(items)==15616 and len(set(identities))==15616
  initial=D/case/'seed/native/initial_connections.tsv';expected={(int(r['net']),int(r['pin'])) for r in csv.DictReader(initial.open(),delimiter='\t')};assert set(identities)==expected
  assert all(math.isfinite(float(r[k])) and float(r[k])>=0 for r in items for k in ('before_s','tree_s'))
  changed=sum(float(r['before_s'])!=float(r['tree_s']) for r in items);handoff_rows.append(dict(case=case,full_required_pins=15616,restored_differing_delays=changed));bindings[str(f)]=sha(f)
 initial_rows=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';cold=D/case/'cold/native/initial_connections.tsv';seed=D/case/'seed/native/initial_connections.tsv';same=cold.read_bytes()==seed.read_bytes();count=len(cold.read_text().splitlines())-1;assert count==15616;initial_rows.append(dict(case=case,connections=count,exact_initial_perpin_delay_and_criticality_equal=same));bindings[str(cold)]=sha(cold);bindings[str(seed)]=sha(seed)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_NATIVE_FEASIBILITY_PAIRS_FULL_COVERAGE_CANONICAL_AND_QOR_CHECKED',rows=rows,handoff_rows=handoff_rows,initial_perpin_comparison=initial_rows,all3_initial_perpin_equal=all(x['exact_initial_perpin_delay_and_criticality_equal'] for x in initial_rows),all3_cold_archived_support_equivalent=all(r['cold'].get('cold_reproduces_archived_native_node_unions',False) for r in rows),all3_full_coverage_QoR_pass=all(r['full_coverage_and_QoR_pair_pass'] for r in rows),complete_matched_workflow_timing_admitted=False,bindings=bindings,scope='Fixed all3 incl failures. CPD diagnostic/nonregress, not constrained timing closure. Native component times exclude fresh prediction/setup/selection/serialization/import proof cost; cannot establish end-to-end gain.'),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
