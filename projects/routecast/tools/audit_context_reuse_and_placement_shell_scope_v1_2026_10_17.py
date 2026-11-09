"""Authenticate historical reuse scopes; do not relabel them as new work."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/context_reuse_and_placement_shell_scope_v1_2026-10-17';D.mkdir(exist_ok=False)
cache={}
def sha(p):
 p=Path(p);st=p.stat();key=(str(p),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  assert p.stat()==st;cache[key]=h.hexdigest()
 return cache[key]
specs=[('xtea_warm_update_hotspots_v1_2026-10-13/research_decision_v1.json','warm_summary'),('xtea_warm_update_pair_v1_2026-10-13/verification.json','warm_pair'),('xtea_placement_feedback_native_v1_2026-10-13/independent_result_verification_v1.json','placement_shell'),('native_live_search_move_sequence_v6_2026-10-07/receipt.json','live_sequence')]
rows=[];docs={};bindings={str(Path(__file__).resolve()):sha(__file__)}
for name,label in specs:
 p=R/'experiments'/name;d=json.loads(p.read_text());bindings[str(p)]=sha(p);docs[label]=d;checks=[]
 for k,h in d.get('bindings',{}).items():
  try:actual=sha(k)
  except FileNotFoundError:actual=None
  checks.append(dict(path=k,expected=h,actual=actual,passes=actual==h))
 rows.append(dict(label=label,path=str(p),direct_binding_checks=checks,all_declared_direct_bindings_pass=all(x['passes'] for x in checks),declared_bindings_count=len(checks),authentication_scope='Current direct declared bindings only; missing binding maps are not recursive input/source authentication.'))
assert all(r['all_declared_direct_bindings_pass'] for r in rows)
w=docs['warm_summary'];shell=docs['placement_shell'];seq=docs['live_sequence']
assert not w['promote_as_end_to_end_acceleration'] and not shell['positive_net_time_gain_proven']
assert shell['all_eight_geometries_selections_and_symmetric_final_gates_reconstructed']
assert len(seq['rows'])==3 and [r['producer']['context_reused'] for r in seq['rows']]==[False,True,True]
out=dict(bindings=bindings,rows=rows,all_present_direct_bindings_pass=True,findings=dict(warm_update=dict(actual_input_change='One real placement swap, shared moved seed/history and fixed pre-move timing; not same-input replay.',all_NET_model_seconds=w['rows']['all']['component_seconds']['model_including_setup_and_output'],local_NET_model_seconds=w['rows']['local']['component_seconds']['model_including_setup_and_output'],scope=w['cost_scope']),placement_shell=dict(candidate_count=8,decisions_actual_and_native_accepted=True,arms=shell['final_arms'],costs=shell['costs'],scope=shell['scope']),live_sequence=dict(changing_prepared_placements=3,resident_context_reused=[False,True,True],total_seconds=seq['total_seconds'],scope=seq['scope'],receipt_has_no_top_level_bindings='bindings' not in seq)),decision='Do not propose graph/context reuse or sketch-gated placement selection as a first implementation. Existing mechanisms lack matched fresh continuous total-time evidence; local scheduling also changes quality. The new proxy-budget native-count improvement does not close these gaps.',next_action='Inspect the largest audited neuron native-label run and exact process clocks to establish the scaling cost envelope versus complete proxy-budget producer/audits. Keep original native routing, label auditing and canonical clocks separate, and do not add nested or differently dated observations into a fake continuous workflow. Use this envelope to choose a genuinely worthwhile optimization or native utility extension rather than rerunning tiny-XTEA losses.',goal_complete=False)
with (D/'verification.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(direct_binding_checks=sum(len(r['direct_binding_checks']) for r in rows),unique_hashed_paths=len(cache),all_present_direct_bindings_pass=True,all_NET_model_seconds=out['findings']['warm_update']['all_NET_model_seconds'],local_NET_model_seconds=out['findings']['warm_update']['local_NET_model_seconds'],shell_costs=shell['costs']),indent=2))
