"""Fixed three-mask budget diagnostic on exact archived pre-abort snapshots."""
import json,sys,heapq
from pathlib import Path
from collections import Counter
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from zero_rc_budget_certificate_graph_v1 import load_graph,candidate_nodes
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_state_preserving_owner_transaction_v1_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';O=E/'prospective_external_family_owner_failure_mask_diagnosis_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);proof=D/'independent_verification_v1.json';v=read(proof);assert v['status']=='ALL_PREFLIGHT_READY_OWNER_TRANSACTIONS_AND_ABORTS_INDEPENDENT_XML_VERIFIED';assert all(sha(p)==h for p,h in v['bindings'].items());bindings=closure([Path(__file__)]);bindings[str(proof)]=sha(proof);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';endpoint=read(matrix)['rows'][0]['endpoint'];graph=Path(read(endpoint)['inputs']['graph']['path']);g=load_graph(graph);caps,types,us,vs,sw,w=(g[k] for k in ['caps','types','us','vs','switches','weights']);bindings[str(graph)]=sha(graph);bindings[str(D/'protocol.json')]=sha(D/'protocol.json');cases=[];data={}
 for spec in read(D/'protocol.json')['cases']:
  case=spec['case'];bp=B/case/'candidate_bank.jsonl';fp=D/case/'failed_search_trees_v1.jsonl';rp=D/case/'result.json';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};f=read(rp)['failure'];net=f['net_id'];assert net not in state;outside=Counter();package=set(spec['package_NETs'])
  for owner,options in bank.items():
   if owner not in package:outside.update(set.intersection(*(candidate_nodes(c,vs) for c in options)))
  usage=Counter(n for c in state.values() for n in candidate_nodes(c,vs));assert all(outside[n]+usage[n]<=caps[n] for n in range(len(caps)));physical={n for n,cap in enumerate(caps) if outside[n]+usage[n]>=cap};root=set(spec['original_root_forbidden_nodes']) if net==2 else set();extra=set(f['extra_forbidden_nodes']);assert root<=extra;records=sorted(bank[net][0]['records'],key=lambda r:r['connection_id']);source=records[0]['source'];assert all(r['source']==source for r in records)
  cases.append(dict(case=case,NET=net,CIDs=[r['connection_id'] for r in records],masks={'capacity_only':sorted(physical),'capacity_plus_root_policy':sorted(physical|root),'capacity_plus_allocation_policy':sorted(physical|extra)},allocation_only_nodes=sorted(extra-physical),root_only_nodes=sorted(root-physical),original_failed_CIDs=f['failed_CIDs']));data[case]=records
  for p in (bp,fp,rp):bindings[str(p)]=sha(p)
 p=O/'protocol.json';p.write_text(json.dumps(dict(cases=cases,bindings=bindings,policy='Exactly capacity-only, capacity+original-root-policy, capacity+all-original-allocation-policy masks on identical verified staged snapshots. All CIDs of each failed NET retain original budgets. Capped full-source potentials and physical witnesses, no new tree installation, owner reassignment, native labels or commits.'),indent=2)+'\n');bindings[str(p)]=sha(p);rows=[]
 for spec in cases:
  records=data[spec['case']];source=records[0]['source'];limit=max(r['budget_integer'] for r in records)+1
  for name,mask in spec['masks'].items():
   blocked=bytearray(len(caps))
   for n in mask:blocked[n]=1
   for n,t in enumerate(types):
    if t=='SOURCE' and n!=source:blocked[n]=1
   dist=array('Q',[limit])*len(caps);parent=array('I',[2**32-1])*len(caps);queue=[]
   if not blocked[source]:dist[source]=0;queue=[(0,source)]
   while queue:
    value,u=heapq.heappop(queue)
    if value!=dist[u] or types[u]=='SINK':continue
    for pos in range(g['offsets'][u],g['offsets'][u+1]):
     eid=g['order'][pos];v=vs[eid]
     if blocked[v]:continue
     d=value+w[sw[eid]]
     if d<dist[v]:dist[v]=d;parent[v]=eid;heapq.heappush(queue,(d,v))
   out=O/spec['case']/name;out.mkdir(parents=True);potential=out/'capped_forward_u64.bin'
   with potential.open('wb') as f:dist.tofile(f)
   queries=[]
   for r in records:
    sink=r['sink'];within=dist[sink]<=r['budget_integer'];edges=[]
    if within:
     u=sink;seen=set()
     while u!=source:
      assert u not in seen;seen.add(u);eid=parent[u];assert eid!=2**32-1;edges.append(eid);u=us[eid]
     edges.reverse();assert sum(w[sw[e]] for e in edges)==dist[sink]
    queries.append(dict(CID=r['connection_id'],source=source,sink=sink,budget_integer=r['budget_integer'],capped_distance=int(dist[sink]),within_budget=within,physical_edge_ids=edges))
   p=out/'queries.json';p.write_text(json.dumps(dict(case=spec['case'],NET=spec['NET'],mask=name,potential_cap=limit,byteorder=sys.byteorder,queries=queries),indent=2)+'\n')
   for q in (potential,p):bindings[str(q)]=sha(q)
   bad=[r['CID'] for r in queries if not r['within_budget']]
   if name=='capacity_plus_allocation_policy':assert bad==spec['original_failed_CIDs']
   row=dict(case=spec['case'],NET=spec['NET'],mask=name,CIDs=len(queries),failed_CIDs=bad,allocation_only_nodes=len(spec['allocation_only_nodes']),root_only_nodes=len(spec['root_only_nodes']),potential=str(potential),queries=str(p));rows.append(row);print('FAILURE_MASK_DIAGNOSTIC',json.dumps({k:v for k,v in row.items() if k not in ['potential','queries']}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='THREE_MASK_BUDGET_DIAGNOSTICS_PREPARED_PENDING_INDEPENDENT_REPLAY',rows=rows,bindings=bindings,scope='Capped distances above budget certify budget failure only, not general unreachability. A capacity-only success removes allocation constraints and does not realize the SAT model. Necessary diagnostic, not predictor quality or utility.'),indent=2)+'\n')
if __name__=='__main__':main()
