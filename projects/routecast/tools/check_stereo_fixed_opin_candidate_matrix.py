"""Authenticate complete 200-query matrix; never infer full-net feasibility."""
import pathlib,json,hashlib,collections
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parent=BASE/'fixed_opin_candidate_matrix';p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text())
 assert sha(parent/'protocol.json')==r['protocol_sha256'];assert sha(parent/'results.json')==r['results_sha256']
 for f,h in p['inputs'].items():assert sha(ROOT/f)==h
 for name,h in p['sources'].items():assert sha(parent/'source'/name)==h
 rows=json.loads((parent/'results.json').read_text());requests=json.loads((BASE/'additional_high_fanout_physical_audit/affected_conflict_connections.json').read_text())['affected_connections'];catalog={v['source_class']:v for v in json.loads((BASE/'source_opin_catalog/catalog.json').read_text())};budgets={v['connection_id']:Fraction(v['delay_seconds_numerator'],v['delay_seconds_denominator']) for v in json.loads((BASE/'additional_high_fanout_exact_budgets/budgets.json').read_text())}
 expected=[(q['connection_id'],pin['node']) for q in requests for pin in catalog[q['source']]['pins']]
 assert len(expected)==200 and [(v['connection_id'],v['opin']) for v in rows]==expected and r['queries']==200
 counts=collections.Counter();found=collections.defaultdict(set);summary=[]
 for q in requests:
  subset=[v for v in rows if v['connection_id']==q['connection_id']];members={v['node']:v for v in catalog[q['source']]['pins']}
  for v in subset:
   assert v['net_id']==q['net_id'];assert Fraction(*v['original_budget'])==budgets[q['connection_id']]
   counts[v['status']]+=1
   assert v['status'] in ['FOUND','UNREACHABLE','NODE_LIMIT']
   if v['status']=='FOUND':
    assert Fraction(*v['delay'])<=budgets[q['connection_id']]
    assert v['physical_edge_ids'][0] in {a['edge_id'] for a in members[v['opin']]['arcs']}
    found[q['connection_id']].add(v['opin'])
   else:assert v['physical_edge_ids'] is None and v['delay'] is None
   if v['opin']==v['original_opin']:assert v['status']=='FOUND'
  summary.append({'connection_id':q['connection_id'],'found_opins':sorted(found[q['connection_id']]),'status_counts':dict(collections.Counter(v['status'] for v in subset))})
 assert dict(counts)=={k:v for k,v in r['status_counts'].items() if v}
 nets={}
 for net in sorted({q['net_id'] for q in requests}):
  cids=[q['connection_id'] for q in requests if q['net_id']==net];common=set.intersection(*(found[cid] for cid in cids));nets[str(net)]={'selected_connection_ids':cids,'common_found_opins':sorted(common),'scope':'only these selected targets, not all targets of net'}
 out=BASE/'fixed_opin_candidate_matrix_completion';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 result={'parent_receipt_sha256':sha(parent/'receipt.json'),'source_sha256':sha(pathlib.Path(__file__)),'queries':200,'complete_expected_query_order':True,'status_counts':dict(counts),'connections':summary,'selected_target_intersections':nets,'scope':'authenticated full query matrix and recorded exact-budget checks; independent original XML new-path audit, ownership, full-net and STA checks still required'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'queries':200,'status_counts':dict(counts),'selected_target_intersections':nets}))
if __name__=='__main__':main()
