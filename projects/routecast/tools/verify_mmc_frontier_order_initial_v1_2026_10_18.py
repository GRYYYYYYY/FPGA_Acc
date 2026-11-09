"""Full admitted-record equality and independent dynamic selection-prefix replay."""
import array,collections,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';root=E/'mmc_frontier_order_initial_v1_2026-10-18';rp=root/'receipt.json';r=json.loads(rp.read_text());assert len(r['rows'])==3;specp=E/'mmc_frontier_order_candidate_protocol_v1_2026-10-18/protocol.json';spec=json.loads(specp.read_text());assert all(sha(p)==h for p,h in spec['bindings'].items());sourcep=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';old={q['connection_id']:q for q in json.loads(sourcep.read_text())['records']};assert sha(sourcep)==r['bindings'][str(sourcep)];idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());gp=E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json';gvp=gp.parent/'independent_verification_v1.json';gpdata=json.loads(gp.read_text());assert sha(gp)==json.loads(gvp.read_text())['bindings'][str(gp)] and sha(idxp)==gpdata['bindings'][str(idxp)];edges=[]
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==gpdata['bindings'][d['path']];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());edges.append(a)
 def pathnodes(q,answer):
  u=q['source'];seen={u}
  for edge in answer['physical_edge_ids']:assert edges[0][edge]==u;u=edges[1][edge];assert u not in seen;seen.add(u)
  assert u==q['sink'];return seen
 data=[];needed=set();bindings={str(p):sha(p) for p in [rp,specp,sourcep,gp,gvp,idxp,Path(__file__)]}
 for row in r['rows']:
  case=row['case'];folder=root/case;candidatep=folder/'initial.json';basep=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained/initial.json';ap=basep.parent.parent/'initial_independent_verification_v1.json';audit=json.loads(ap.read_text());assert audit['status']=='pass' and audit['all115572V2budgets_matched'] and sha(basep)==audit['bindings'][str(basep)];candidate=json.loads(candidatep.read_text());base=json.loads(basep.read_text());assert sha(candidatep)==row['files'][str(candidatep)];assert candidate['records']==base['records'] and len(base['records'])==115572;differing={k for k in candidate.keys()|base.keys() if candidate.get(k)!=base.get(k)};assert differing=={'scope','initializer_policy'};assert candidate['initializer_policy']=='nearest_projected_retained_frontier_v1' and not candidate['eligible_for_legal_route_commit']
  for name in ['floors.json','history.json']:assert sha(folder/name)==sha(basep.parent/name)==row['files'][str(folder/name)]
  bindings[str(ap)]=sha(ap);bindings[str(basep)]=sha(basep);queries={q['connection_id']:q for q in candidate['records']};assert set(queries)==set(old)==set(range(115572));dirty={q['net_id'] for c,q in queries.items() if (q['source'],q['sink'])!=(old[c]['source'],old[c]['sink'])};groups=collections.defaultdict(list)
  for c,q in queries.items():groups[q['net_id']].append(c)
  resultp=folder/'initializer_returns.json';tracep=folder/'selection_trace.jsonl';assert sha(resultp)==row['files'][str(resultp)] and sha(tracep)==row['files'][str(tracep)];results=json.loads(resultp.read_text());trace=[json.loads(s) for s in tracep.read_text().splitlines()];assert {x['net_id'] for x in results}==dirty;prefix={}
  for item in results:
   net=item['net_id'];v=item['result'];assert not v['whole_NET_fallback'];eligible=sorted(c for c in groups[net] if (queries[c]['source'],queries[c]['sink'])==(old[c]['source'],old[c]['sink']));assert eligible==v['retained_connection_ids']==v['attempted_retained_connection_ids'];answers={int(c):a for c,a in v['answers'].items()};assert set(answers)==set(groups[net]);members={}
   for c,a in answers.items():assert a==queries[c]['answer'];members[c]=pathnodes(queries[c],a);needed.update(members[c])
   assert set(v['owner_nodes'])==set().union(*members.values());prefix[net]=(eligible,members)
  payload={k:v for k,v in candidate.items() if k not in differing};payloadhash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest();data.append((row,queries,groups,results,trace,prefix,differing,payloadhash))
 graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)==idx['graph_sha256']==r['bindings'][str(graph)];geo={};stack=[]
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   node=int(n.get('id'))
   if node in needed:
    loc=n.find('loc');assert int(n.get('capacity'))>0;geo[node]=(n.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')))
   parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert set(geo)==needed;rows=[];steps=orders=0
 for row,queries,groups,results,trace,prefix,differing,payloadhash in data:
  cursor=0;changed_orders=0
  for item in results:
   net=item['net_id'];eligible,members=prefix[net];source=queries[groups[net][0]]['source'];tree={source}
   for c in eligible:tree.update(members[c])
   remaining=set(groups[net])-set(eligible);chosen=[]
   while remaining:
    scores={}
    for c in remaining:
     b=geo[queries[c]['sink']];dist=[]
     for n in tree:
      a=geo[n]
      if a[0] not in ['SOURCE','OPIN','CHANX','CHANY'] or a[5]!=b[5]:continue
      dist.append(max(0,max(a[1],b[1])-min(a[2],b[2]))+max(0,max(a[3],b[3])-min(a[4],b[4])))
     scores[c]=min(dist) if dist else None
    c=min(remaining,key=lambda cid:(scores[cid] is None,0 if scores[cid] is None else scores[cid],cid));before,after=trace[cursor:cursor+2];cursor+=2;assert before['phase']=='select' and before['net_id']==net and before['connection_id']==c and dict(before['candidates'])==scores and before['tree_nodes']==len(tree);assert after['phase']=='expanded' and after['connection_id']==c and after['net_id']==net and after['committed'] and after['status']=='COMMITTED' and after['path_edge_ids']==queries[c]['answer']['physical_edge_ids'] and after['raw']==queries[c]['answer']['delay']<=queries[c]['budget_integer'];remaining.remove(c);tree.update(members[c]);chosen.append(c);steps+=1
   assert item['result']['repair_calls']==len(chosen);changed_orders+=chosen!=sorted(chosen)
  assert cursor==len(trace) and changed_orders==row['NETs_with_changed_repair_order'];orders+=changed_orders;rows.append(dict(case=row['case'],all115572_records_and_physical_RC_budget_admission_transferred_by_exact_equality=True,all_numeric_initial_state_fields_equal_to_baseline=True,metadata_differences=sorted(differing),routing_payload_sha256=payloadhash,repair_steps_verified=row['repair_calls'],NETs_with_changed_order=changed_orders,changed_path_CIDs=0));print('INDEPENDENT FIXED FRONTIER ORDER PASS',row['case'],changed_orders,0,flush=True)
 assert steps==283 and orders==33
 for p,h in r['bindings'].items():assert sha(p)==h
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all3_complete_admitted_record_equality_and283_dynamic_frontier_selections_verified',bindings=bindings,rows=rows,repair_steps_verified=steps,NETs_with_changed_order=orders,scope='Exact equality transfers existing original-XML/Fraction path, budget and NET accounting admission for all346716records. Dynamic order independently replayed from source path prefixes and original XML geometry. Only scope/initializer metadata differ. This candidate changes no predictive initial routing data; no quality improvement or native policy promotion.'),f,indent=2)
if __name__=='__main__':main()
