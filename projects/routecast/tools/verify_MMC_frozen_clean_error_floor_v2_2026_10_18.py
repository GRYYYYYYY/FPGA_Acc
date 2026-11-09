"""Check fixed-clean premise and exact integral distance-to-interval lower bound."""
import pathlib,json,hashlib,sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 out=R/'experiments/mmc_frozen_clean_error_floor_v1_2026-10-18';r=json.loads((out/'results_v2.json').read_text());bindings={str(out/'results_v2.json'):sha(out/'results_v2.json'),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 def load(p):
  p=pathlib.Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 topo=R/'experiments/mmc_endpoint_geometry_topology_v2_2026-10-18';proof=load(topo/'independent_verification_v1.json');receipt=load(topo/'receipt.json');assert proof['bindings'][str(topo/'receipt.json')]==sha(topo/'receipt.json');assert proof['XML_edges_verified']==8097539
 idx=load(R/'experiments/real_joint_full_score_v2_2026-10-18/graph_index.json');edge=idx['arrays']['edge_destination'];assert receipt['bindings'][edge['path']]==edge['sha256']==sha(edge['path'])
 # Exhaustive small integer oracle independent of the closed-form expression.
 for d in range(6):
  for c in range(8):
   for t in range(10):assert min(abs(c+x-t) for x in range(d+1))==max(c-t,t-c-d,0)
 for row in r['cases']:
  case=row['case'];warm=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';dirty=set(load(warm/'verification.json')['dirty_nets']);initial=load(warm/'initial.json');clean={x['connection_id']:x for x in initial['records'] if x['net_id'] not in dirty}
  for p in [warm.parent/'feedback_on/native_retained/sketch.json']:
   f=load(p);actual={x['connection_id']:x for x in f['records'] if x['net_id'] not in dirty};assert actual==clean
  assert all(x['clean_NETs']>x['target'] and x['unavoidable_absolute_error']==x['clean_NETs']-x['target'] for x in row['witnesses'])
 assert all(sha(k)==h for k,h in bindings.items())
 v=dict(status='fixed_clean_premise_original_candidate_all3_cases_and_interval_oracle_verified',bindings=bindings,small_integer_oracle_cases=480,original_XML_edge_certificate_chain_bound=True,scope='Certifies frozen-clean premise and bound algebra. Producer computes complete channel totals; no independent full-total reconstruction claimed. Not a bound on Spearman or hotspot precision.',accepted_gain=False)
 (out/'verification_v2.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'])
if __name__=='__main__':main()
