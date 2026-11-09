"""Revalidate every native/trace/canonical/readback and fixed component gate."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_native_evaluation_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 um=read(D/'utility_manifest.json');cm=read(D/'cold_manifest.json');prior=read(D/'utility_review_v1.json');assert prior['all9_available'] and prior['all9_zero_equivalent'];bindings={str(p):sha(p) for p in [Path(__file__),D/'utility_manifest.json',D/'cold_manifest.json',D/'utility_review_v1.json']};rows=[];native_count=0
 for c in cm['cases']:
  case=c['target_case'];cold=Path(c['output']);coldproof=read(cold/'verification.json');assert coldproof['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';values={}
  for n,h in coldproof['bindings'].items():assert sha(Path(n))==h
  bindings[str(cold/'verification.json')]=sha(cold/'verification.json');native_count+=1
  for arm in ['disabled','zero','forecast']:
   job=next(j for j in um['cases'] if j['target_case']==case and j['utility_arm']==arm);out=Path(job['output']);v=read(out/'verification.json');assert v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and v['independent_trace_replay_pass'];assert v['canonical']['semantic_consistency_gate_pass']
   for n,h in v['bindings'].items():assert sha(Path(n))==h
   for n,h in v['canonical']['files'].items():assert sha(Path(n))==h
   replay=read(out/'trace_replay.json');assert replay['exact_native_work_counters_equal'] and replay['final_physical_NET_unions_equal'] and replay['work']==v['native_work']
   if arm!='disabled':assert v['preload_state']['all_nodes_checked']==job['graph_nodes'] and v['preload_state']['all_bits_match_fixed_one_pseudo_iteration']
   values[arm]=v;bindings[str(out/'verification.json')]=sha(out/'verification.json');native_count+=1
  z,on=values['zero'],values['forecast'];off=values['disabled'];disabled=Path(next(j['output'] for j in um['cases'] if j['target_case']==case and j['utility_arm']=='disabled'));zero=Path(next(j['output'] for j in um['cases'] if j['target_case']==case and j['utility_arm']=='zero'));assert sha(cold/'output.route')==sha(disabled/'output.route')==sha(zero/'output.route')
  for key in ['iterations','wirelength','diagnostic_cpd_ns']:assert coldproof[key]==off[key]==z[key]
  assert off['native_work']==z['native_work'];nonreg=[on['native_work'][k]<=z['native_work'][k] for k in ['NET_operations','connection_operations','heap_pushes','heap_pops']];strict=[on['native_work'][k]<z['native_work'][k] for k in ['NET_operations','connection_operations','heap_pushes','heap_pops']];passed=all(nonreg) and any(strict) and on['wirelength']<=z['wirelength'] and on['diagnostic_cpd_ns']<=z['diagnostic_cpd_ns']+1e-12;original=next(r for r in prior['rows'] if r['case']==case);assert passed==original['pass_component_gate'];rows.append({'case':case,'cold_disabled_zero_route_bytes_equal':True,'native_full_and_trace_and_readback_pass':True,'component_gate':passed,'zero':{k:z[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_work']},'forecast':{k:on[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_work']}})
 assert native_count==36 and len(rows)==9
 result={'status':'ALL36_NATIVE_RECEIPTS_AND9_COLD_DISABLED_ZERO_PARITIES_COMPONENT_GATES_REVALIDATED','rows':rows,'native_cases':native_count,'component_gate_passes':sum(r['component_gate'] for r in rows),'all9_component_gate_pass':all(r['component_gate'] for r in rows),'new_acceptance_rule_introduced':False,'candidate_promoted':False,'full_paid_gain_proven':False,'strict_unseen_admitted':False,'bindings':bindings};(D/'independent_native_review_v1.json').write_text(json.dumps(result,indent=2)+'\n');print('NATIVE_CONTROLS_REVALIDATED',native_count,result['component_gate_passes'])
if __name__=='__main__':main()
