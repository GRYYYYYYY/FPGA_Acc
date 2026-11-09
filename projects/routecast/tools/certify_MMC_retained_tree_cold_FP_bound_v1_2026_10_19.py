"""Monotone lower bound from fixed retained ownership; not an original quality-gate certificate."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from audit_native_route import NET,NODE
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def sets(path,names,channels):
 out={};name=None
 with path.open() as f:
  for line in f:
   m=NET.match(line)
   if m:
    name=m[2]
    if name in names:assert name not in out;out[name]=set()
   m=NODE.match(line)
   if m and int(m[1]) in channels:
    assert name in out;out[name].add(int(m[1]))
 assert set(out)==names;return out

def main():
 D=R/'experiments/mmc_unchanged_NET_route_churn_v1_2026-10-19/review.json';d=json.loads(D.read_text());assert d['status']=='ALL3_FULL_PHYSICAL_EDGE_AND_CHANNEL_UNION_CHURN_WITH_EXACT_SIGNED_OWNERSHIP_DECOMPOSITION'
 for p,h in d['bindings'].items():assert sha(pathlib.Path(p))==h
 M=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19';protocol=json.loads((M/'protocol.json').read_text());geometry=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());source=pathlib.Path(geometry['previous_native_route']);graph=pathlib.Path(json.loads((M/'common_context.json').read_text())['graph']);channels=set();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
    assert int(e.get('capacity'))==1;channels.add(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720;meta=json.loads(pathlib.Path(protocol['cases'][0]['endpoint']).read_text());names={meta['net_names'][str(q['net_id'])] for q in meta['connections']};original=sets(source,names,channels);bindings={str(p):sha(p) for p in [D,M/'protocol.json',source,graph,pathlib.Path(__file__).resolve()]};rows=[]
 for plan in protocol['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());qs={q['connection_id']:q for q in meta['connections']};dirty={meta['net_names'][str(qs[cid]['net_id'])] for cid in plan['changed_CIDs']};stable=names-dirty;C=R/'experiments/mmc_reference_incremental_astar_canonical_v3_2026-10-19'/case;candidate=C/'canonical/design.route';cp=C/'receipt.json';c=json.loads(cp.read_text());assert c['files'][str(candidate)]==sha(candidate);cold=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case/'cold/output.route';assert d['bindings'][str(cold)]==sha(cold);actual=sets(cold,names,channels);prediction=sets(candidate,names,channels);assert all(prediction[n]==original[n] for n in stable)
  fixed=set().union(*(original[n] for n in stable));truth=set().union(*actual.values());pred=set().union(*prediction.values());forced=fixed-truth;fp=pred-truth;fn=truth-pred;assert forced<=fp and len(fp)+len(fn)==len(pred^truth);implicated={n for n in stable if original[n]&forced};assert forced==set().union(*(original[n]-truth for n in implicated))
  row=dict(case=case,unchanged_endpoint_NETs=len(stable),fixed_retained_CHANNEL_nodes=len(fixed),unavoidable_FP_CHANNEL_nodes=len(forced),unchanged_NETs_requiring_some_CHANNEL_change_for_exact_cold_occupancy=len(implicated),current_candidate_FP_CHANNEL_nodes=len(fp),current_candidate_FN_CHANNEL_nodes=len(fn),current_candidate_CHANNEL_L1=len(fp)+len(fn),bound_on_fraction_of_candidate_FP_fixed=len(forced)/len(fp) if fp else None,all_unchanged_NET_CHANNEL_unions_exact_prior=True,original_quality_gate_infeasibility_proven=False);rows.append(row)
  for p in [ep,candidate,cp,cold]:bindings[str(p)]=sha(p)
  print('FIXED_TREE_FP_BOUND',json.dumps(row),flush=True)
 O=R/'experiments/mmc_retained_tree_cold_FP_bound_v1_2026-10-19';O.mkdir(exist_ok=False);result=dict(status='ALL3_FIXED_RETAINED_CHANNEL_FALSE_POSITIVE_LOWER_BOUNDS_CERTIFIED',cases=rows,bindings=bindings,proof='All positive CHANNEL capacities are one. Every fixed unchanged-NET prior CHANNEL remains occupied under any additions or replacements confined to changed-endpoint NETs. If cold occupancy there is zero, its normalized absolute error is at least one. Thus fixed_union minus cold_union is an unavoidable false-positive set. Fixed owner NETs are disjoint, so each implicated NET must change some CHANNEL to reproduce exactly the cold occupancy.',scope='Exact future-label reproduction lower bound only, using exposed labels for diagnosis. Does not prove original four-metric quality gate infeasible, cold routing uniquely correct, changed NETs cannot improve scores, or global rerouting necessary for legality. No label/metric/budget changes or new forecasts.')
 (O/'review.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
