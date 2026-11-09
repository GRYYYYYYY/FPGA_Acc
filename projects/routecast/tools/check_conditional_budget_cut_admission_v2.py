"""Real all-CID premise checks, including sibling-CID cache separation."""
import json
from pathlib import Path
from collections import Counter
from conditional_budget_cut_admission_v2 import verified_store,admit,ContextMismatch
from zero_rc_budget_certificate_graph_v1 import load_graph,candidate_nodes
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'conditional_budget_cut_admission_contract_v2_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';SOURCES=[E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19',E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19',E/'prospective_external_family_all_CID_terminal_budget_domains_v1_2026-10-19']
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);clauses=[];bindings={str(p):sha(p) for p in (Path(__file__).resolve(),R/'tools/conditional_budget_cut_admission_v2.py',R/'tools/conditional_budget_cut_admission_v1.py',H/'protocol.json')};unbound=0
 for i,d in enumerate(SOURCES):
  artifact=d/'learned_conditional_budget_constraints_v1.json';proof=d/'independent_verification_v1.json';clauses.extend(verified_store(artifact,proof));bindings[str(artifact)]=sha(artifact);bindings[str(proof)]=sha(proof);p=D/f'unbound_artifact_{i}.json';p.write_text(artifact.read_text())
  try:verified_store(p,proof)
  except ValueError:unbound+=1
  else:raise AssertionError('unbound proof artifact accepted')
  bindings[str(p)]=sha(p)
 matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph=Path(read(inputs['w160/episode_01']['endpoint'])['inputs']['graph']['path']);g=load_graph(graph);digest=sha(graph);contexts={}
 for spec in read(H/'protocol.json')['cases']:
  case=spec['case'];bp=B/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};outside=Counter()
  for net,options in bank.items():
   if net not in set(spec['package_NETs']):outside.update(set.intersection(*(candidate_nodes(c,g['vs']) for c in options)))
  contexts[case]=(bank,outside);bindings[str(bp)]=sha(bp)
 admitted=sibling_rejects=budget_rejects=0
 for clause in clauses:
  bank,outside=contexts[clause['case']];records=bank[clause['NET']][0]['records'];query=next(q for q in records if q['connection_id']==clause['connection_id']);admit(clause,clause['case'],digest,query,outside);admitted+=1;bad=dict(query,budget_integer=query['budget_integer']+1)
  try:admit(clause,clause['case'],digest,bad,outside)
  except ContextMismatch as error:assert str(error)=='budget';budget_rejects+=1
  else:raise AssertionError('changed original budget accepted')
  sibling=next((q for q in records if q['connection_id']!=query['connection_id']),None)
  if sibling:
   try:admit(clause,clause['case'],digest,sibling,outside)
   except ContextMismatch as error:assert str(error)=='connection';sibling_rejects+=1
   else:raise AssertionError('same NET different CID proof reused')
 bindings[str(matrix)]=sha(matrix);bindings[str(graph)]=sha(graph);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='REVERSE_CUT_AND_ALL_CID_INGRESS_PROOF_ADMISSION_WITH_SIBLING_SEPARATION_VERIFIED',valid_contexts=admitted,budget_mismatch_rejections=budget_rejects,same_NET_sibling_CID_rejections=sibling_rejects,unbound_artifact_rejections=unbound,bindings=bindings,scope='Reuses exact v1 case/graph/NET/source/sink/budget/outside premise checks while admitting independently verified forward-terminal-domain proof family. No proof can be reused merely because NET identity matches.'),indent=2)+'\n');print(dict(valid=admitted,budget_rejects=budget_rejects,sibling_rejects=sibling_rejects,unbound_artifacts=unbound),flush=True)
if __name__=='__main__':main()
