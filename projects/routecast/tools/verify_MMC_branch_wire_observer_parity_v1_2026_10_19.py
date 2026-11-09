"""All80 exact semantic parity plus accounting identities and observer summary."""
import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[1];A=R/'experiments/mmc_prior_budget_branch_wire_pilot_v1_2026-10-19';O=R/'experiments/mmc_prior_budget_branch_wire_diag_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 proof=A/'independent_verification_v1.json';pv=json.loads(proof.read_text());assert pv['status']=='FULL115572_CONNECTION_XML_RC_CAPACITY_AND_ALL80_RESOURCE_TRANSACTIONS_PASS';ap=A/'events.jsonl';assert pv['bindings'][str(ap)]==sha(ap);old=[json.loads(x) for x in ap.read_text().splitlines()];new=[json.loads(x) for x in (O/'events.jsonl').read_text().splitlines()];assert len(old)==len(new)==80;fields=[]
 receipt=R/'build/native_bounded_wire_diag_v1_2026-10-19/receipt.json';build=json.loads(receipt.read_text())
 for p,h in build['bindings'].items():assert sha(pathlib.Path(p))==h
 code=(receipt.parent/'kernel.cpp').read_text();extra='\nextern "C" uint64_t rc_diag_count(void* ptr,uint64_t index){return index<22?static_cast<Context*>(ptr)->diag[index]:0;}\n';assert code.endswith(extra);code=code[:-len(extra)]
 for baseline,instrumented in reversed(build['reverse_substitutions']):assert code.count(instrumented)==1;code=code.replace(instrumented,baseline)
 assert code==(R/'tools/native_bounded_wire_search_v1.cpp').read_text()
 for a,b in zip(old,new):
  assert {k:v for k,v in a.items() if k!='seconds'}=={k:v for k,v in b.items() if k not in ['seconds','diagnostics']}
  if 'diagnostics' not in b:continue
  d=b['diagnostics'];assert d['created_kept']+d['created_unkept']==b['labels_created']==d['created_zero_wire']+d['created_positive_wire']==d['distinct_labeled_nodes']+d['additional_labels_on_existing_node']==d['alive_labels_at_finish']+d['dead_labels_at_finish'];assert d['expanded_kept']+d['expanded_unkept']==b['labels_expanded']==d['expanded_zero_wire']+d['expanded_positive_wire']
  if b['status']=='LABEL_LIMIT':fields.append(dict(connection_id=b['connection_id'],net_id=b['net_id'],created=b['labels_created'],expanded=b['labels_expanded'],**d))
 for name in ['final_unique_NET_occupancy.json']+[f'net_{n}_tree.json' for n in [1395,1400,1404,1754,2925]]:assert json.loads((A/name).read_text())==json.loads((O/name).read_text())
 sums={k:sum(x[k] for x in fields) for k in ['created','expanded','created_kept','created_unkept','created_zero_wire','created_positive_wire','expanded_kept','expanded_unkept','expanded_zero_wire','expanded_positive_wire','distinct_labeled_nodes','additional_labels_on_existing_node','multi_frontier_insertions','alive_labels_at_finish','dead_labels_at_finish']};summary=dict(sums=sums,max_live_frontier_at_any_node=max(x['max_live_frontier_at_node'] for x in fields),limit_expanding_wire_values=sorted(set(x['limit_expanding_wire'] for x in fields)),zero_wire_expansion_fraction=sums['expanded_zero_wire']/sums['expanded'],additional_label_fraction=sums['additional_labels_on_existing_node']/sums['created'])
 bindings={str(p):sha(p) for p in [proof,ap,O/'events.jsonl',O/'results.json',receipt,pathlib.Path(__file__).resolve()]+[O/f'net_{n}_tree.json' for n in [1395,1400,1404,1754,2925]]+[O/'final_unique_NET_occupancy.json']}
 with (O/'independent_parity_verification_v1.json').open('x') as f:json.dump(dict(status='ALL80_OBSERVER_SEMANTIC_PARITY_AND_FINAL_STATE_EQUAL_ORIGINAL_XML_AUDIT',exact_kernel_reverse_reconstruction=True,queries=80,instrumented_queries=22,label_limit_queries=len(fields),summary=summary,rows=fields,bindings=bindings,scope='Original80 frozen queries only. Counters do not prove absence of a feasible better branch. Final physical/budget/capacity proof transferred by complete state equality to original full XML audit.'),f,indent=2)
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
