"""Independent Expat original-graph path and lower-bound verification for mask ablation."""
import json,sys,xml.parsers.expat
from pathlib import Path
from fractions import Fraction
from array import array
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_reservation_failure_mask_diagnosis_v1_2026-10-19';H=E/'prospective_external_family_reservation_only_owner_transaction_v1_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='TWO_MASK_BUDGET_DIAGNOSTICS_PREPARED_PENDING_INDEPENDENT_REPLAY'
 for receipt in [proof,protocol]:assert all(sha(p)==h for p,h in receipt['bindings'].items())
 graph=next(Path(p) for p in proof['bindings'] if p.endswith('/rr_graph.xml'));caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[];active={};timings=0
 def start(name,attrs):
  nonlocal timings
  parent=stack[-1] if stack else None;stack.append(name)
  if name=='node' and parent=='rr_nodes':assert int(attrs['id'])==len(caps);caps.append(int(attrs['capacity']));types.append(attrs['type'])
  elif name=='timing' and parent=='node':assert Fraction(attrs['R'])==Fraction(attrs['C'])==0;timings+=1
  elif name=='switch' and parent=='switches':active['switch']=int(attrs['id'])
  elif name=='timing' and parent=='switch':
   assert all(Fraction(attrs.get(k,'0'))==0 for k in ['R','Cin','Cout','Cinternal']);w=Fraction(attrs.get('Tdel','0'))*10**18;assert w.denominator==1 and w>=0;weights[active['switch']]=w.numerator
  elif name=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']));switches.append(int(attrs['switch_id']))
 def end(name):assert stack.pop()==name
 parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 assert timings==len(caps);n=len(caps);prior={r['case']:r for r in read(H/'protocol.json')['cases']};assert [r['case'] for r in protocol['cases']]==list(prior);bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'verification.json',D/'protocol.json',H/'protocol.json',graph]};rows=[];inequalities=paths=connections=0
 def owned(c):
  s={r['source'] for r in c['records']}
  for r in c['records']:s.update(vs[e] for e in r['answer']['physical_edge_ids'])
  return s
 for spec in protocol['cases']:
  case=spec['case'];bp=B/case/'candidate_bank.jsonl';fp=H/case/'failed_search_trees_v1.jsonl';rp=H/case/'result.json';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};failure=read(rp)['failure'];net=failure['net_id'];assert spec['NET']==net and net not in state;package=set(prior[case]['package_NETs']);outside=Counter()
  for owner,options in bank.items():
   if owner not in package:outside.update(set.intersection(*(owned(c) for c in options)))
  usage=Counter(n for c in state.values() for n in owned(c));assert all(outside[u]+usage[u]<=caps[u] for u in range(n));physical={u for u,cap in enumerate(caps) if outside[u]+usage[u]>=cap};root=set(prior[case]['original_root_forbidden_nodes']) if net==2 else set();extra=set(failure.get('extra_forbidden_nodes',[]));assert root<=extra;expected={'capacity_only':physical,'capacity_plus_reservation_policy':physical|extra};assert spec['masks']=={k:sorted(v) for k,v in expected.items()};assert spec['reservation_only_nodes']==sorted(extra-physical) and spec['root_only_nodes']==sorted(root-physical);records=sorted(bank[net][0]['records'],key=lambda r:r['connection_id']);assert spec['CIDs']==[r['connection_id'] for r in records];source=records[0]['source'];limit=max(r['budget_integer'] for r in records)+1;variants=[]
  for name,mask in expected.items():
   pp=D/case/name/'capped_forward_u64.bin';qp=D/case/name/'queries.json';q=read(qp);assert (q['case'],q['NET'],q['mask'],q['potential_cap'])==(case,net,name,limit);assert pp.stat().st_size==n*8;phi=array('Q')
   with pp.open('rb') as f:phi.fromfile(f,n)
   if q['byteorder']!=sys.byteorder:phi.byteswap()
   assert max(phi)<=limit;blocked=bytearray(u in mask or (types[u]=='SOURCE' and u!=source) for u in range(n));checked=0
   if blocked[source]:assert all(v==limit for v in phi)
   else:assert phi[source]==0
   for u,v,s in zip(us,vs,switches):
    if blocked[u] or blocked[v] or types[u]=='SINK':continue
    assert phi[v]<=phi[u]+weights[s];checked+=1
   assert len(q['queries'])==len(records);bad=[];localpaths=0
   for original,entry in zip(records,q['queries']):
    cid,sink,budget=original['connection_id'],original['sink'],original['budget_integer'];assert (entry['CID'],entry['source'],entry['sink'],entry['budget_integer'])==(cid,source,sink,budget);assert entry['capped_distance']==phi[sink] and entry['within_budget']==(phi[sink]<=budget);assert types[sink]=='SINK'
    if entry['within_budget']:
     edges=entry['physical_edge_ids'];assert edges and not blocked[source];u=source;seen={u};value=0
     for i,eid in enumerate(edges):
      assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert not blocked[v] and v not in seen and caps[v]>0
      if i<len(edges)-1:assert types[v] not in ['SOURCE','SINK']
      seen.add(v);value+=weights[switches[eid]];u=v
     assert u==sink and value==phi[sink]<=budget;localpaths+=1
    else:assert not entry['physical_edge_ids'];bad.append(cid)
   if name=='capacity_plus_reservation_policy':assert bad==failure['failed_CIDs']==spec['original_failed_CIDs']
   row=dict(case=case,NET=net,mask=name,CIDs=len(records),failed_CIDs=bad,forward_edge_inequalities_verified=checked,physical_paths_verified=localpaths);rows.append(row);variants.append(row);inequalities+=checked;paths+=localpaths;connections+=len(records)
   for p in [pp,qp]:bindings[str(p)]=sha(p)
   print('MASK_DIAGNOSTIC_INDEPENDENT_PASS',json.dumps(row),flush=True)
  assert set(variants[0]['failed_CIDs'])<=set(variants[1]['failed_CIDs'])
  for p in [bp,fp,rp]:bindings[str(p)]=sha(p)
 assert len(rows)==len(proof['rows'])
 for observed,prepared in zip(rows,proof['rows']):
  for k in ['case','NET','mask','CIDs','failed_CIDs']:assert observed[k]==prepared[k]
 assert all(sha(p)==h for p,h in bindings.items());out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL3_TWO_MASK_RESERVATION_FAILURES_ORIGINAL_XML_INDEPENDENTLY_VERIFIED',rows=rows,connections_verified=connections,physical_paths_verified=paths,forward_edge_inequalities_verified=inequalities,bindings=bindings,scope='Exact budget outcome under each fixed mask. Negative certificates prove above-original-budget only; success under relaxed masks is not SAT model realization or tree/whole-package completion. Outside occupancy is finite-bank conditional; quality and utility gates unchanged.'),indent=2)+'\n')
if __name__=='__main__':main()
