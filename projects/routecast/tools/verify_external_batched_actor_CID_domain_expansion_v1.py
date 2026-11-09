"""Expat original-graph replay: physical witnesses and Bellman lower bounds."""
import json,sys,hashlib,xml.parsers.expat
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';D=E/'prospective_external_family_batched_actor_CID_domain_expansion_v1_2026-10-19';P=E/'prospective_external_family_actor_expanded_pure_batch_ownership_v1_2026-10-19/physical_proposal_preflight_v1.json'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='ALL_RELEVANT_NET_CID_TERMINAL_BUDGET_DOMAINS_PREPARED_PENDING_INDEPENDENT_REPLAY'
 for receipt in (proof,protocol):assert all(sha(p)==h for p,h in receipt['bindings'].items())
 coreproof=H/'failed_search_contexts_verification_v1.json';actual_failures={r['case']:r for r in read(coreproof)['rows']};packages={r['case']:set(r['package_NETs']) for r in read(H/'protocol.json')['cases']};graph=next(Path(p) for p in proof['bindings'] if p.endswith('/rr_graph.xml'));caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[];active={};timings=0
 def start(name,attrs):
  nonlocal timings
  parent=stack[-1] if stack else None;stack.append(name)
  if name=='node' and parent=='rr_nodes':assert int(attrs['id'])==len(caps);caps.append(int(attrs['capacity']));types.append(attrs['type'])
  elif name=='timing' and parent=='node':assert Fraction(attrs['R'])==Fraction(attrs['C'])==0;timings+=1
  elif name=='switch' and parent=='switches':active['switch']=int(attrs['id'])
  elif name=='timing' and parent=='switch':
   assert all(Fraction(attrs.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));w=Fraction(attrs.get('Tdel','0'))*10**18;assert w.denominator==1 and w>=0;weights[active['switch']]=w.numerator
  elif name=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']));switches.append(int(attrs['switch_id']))
 def end(name):assert stack.pop()==name
 parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 assert timings==len(caps) and len(us)==len(vs)==len(switches) and all(s in weights for s in switches);n=len(caps);bindings={str(p):sha(p) for p in (D/'verification.json',D/'protocol.json',coreproof,H/'protocol.json',graph,Path(__file__).resolve())};rows=[];clauses=[];positive=negative=inequalities=0
 def owned(c):
  ns={r['source'] for r in c['records']}
  for r in c['records']:ns.update(vs[e] for e in r['answer']['physical_edge_ids'])
  return ns
 known=[]
 for directory in (E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19',E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19'):
  pp=directory/'independent_verification_v1.json';prior=read(pp);assert all(sha(p)==h for p,h in prior['bindings'].items());known.extend(read(directory/'learned_conditional_budget_constraints_v1.json')['clauses']);bindings[str(pp)]=sha(pp)
 preflight=read(P);assert all(sha(q)==h for q,h in preflight['bindings'].items());bindings[str(P)]=sha(P);missing={r['case']:r['requirements']['actors_missing_all_CID_domain_proofs'] for r in preflight['rows']}
 contexts={};expected_keys=[]
 for spec in protocol['cases']:
  case=spec['case'];bp=B/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets)
   if net not in packages[case]:outside.update(common)
  relevant=sorted(missing[case]);assert spec['queried_NETs']==relevant;stamp=hashlib.sha256(json.dumps(sorted(outside.items()),separators=(',',':')).encode()).hexdigest();assert spec['outside_unique_NET_occupancy_sha256']==stamp
  for net in relevant:
   assert spec['connections'][str(net)]==sorted(r['connection_id'] for r in bank[net][0]['records']);expected_keys.append((case,net))
  contexts[case]=(bank,outside,stamp);bindings[str(bp)]=sha(bp)
 assert [(r['case'],r['NET']) for r in proof['rows']]==expected_keys;incoming={}
 for eid,v in enumerate(vs):
  if types[v]=='SINK':incoming.setdefault(v,[]).append(eid)
 learned=[];witnesses_verified=0
 for item in proof['rows']:
  case,net=item['case'],item['NET'];bank,outside,stamp=contexts[case];records=sorted(bank[net][0]['records'],key=lambda r:r['connection_id']);source=records[0]['source'];assert all(r['source']==source for r in records);limit=max(r['budget_integer'] for r in records)+1;path=D/case/f'NET_{net}'/'forward_lower_bound_u64.bin';assert str(path)==item['potential_file'] and path.stat().st_size==n*8 and item['potential_cap']==limit;phi=array('Q')
  with path.open('rb') as f:phi.fromfile(f,n)
  first=read(item['terminal_domains'][0]['certificate'])
  if first['byteorder']!=sys.byteorder:phi.byteswap()
  assert phi.itemsize==8 and len(phi)==n and max(phi)<=limit and phi[source]==0;blocked=bytearray(n)
  for node,cap in enumerate(caps):blocked[node]=int(outside[node]>=cap or (types[node]=='SOURCE' and node!=source))
  assert not blocked[source] and types[source]=='SOURCE';checked=0
  for u,v,switch in zip(us,vs,switches):
   if blocked[u] or blocked[v] or types[u]=='SINK':continue
   assert phi[v]<=phi[u]+weights[switch],(case,net,u,v);checked+=1
  inequalities+=checked;assert item['connections']==len(records) and len(item['terminal_domains'])==len(records);domains=[];local_witnesses=0
  for q,entry in zip(records,item['terminal_domains']):
   sink,budget,cid=q['sink'],q['budget_integer'],q['connection_id'];certificate_path=D/case/f'NET_{net}'/f'CID_{cid}.json';assert entry['CID']==cid and entry['certificate']==str(certificate_path);certificate=read(certificate_path);assert (certificate['case'],certificate['NET'],certificate['CID'],certificate['source'],certificate['sink'],certificate['budget_integer'])==(case,net,cid,source,sink,budget);assert certificate['potential_cap']==limit and certificate['forward_potential_file']==str(path) and certificate['forward_potential_sha256']==sha(path) and certificate['byteorder']==first['byteorder'] and certificate['itemsize']==8;assert types[sink]=='SINK' and not blocked[sink];edges=incoming.get(sink,[]);assert certificate['all_incoming_edge_ids']==edges;eligible=set()
   for eid in edges:
    u=us[eid];assert types[u]=='IPIN' and caps[u]==1
    if not blocked[u] and phi[u]+weights[switches[eid]]<=budget:eligible.add(u)
   assert eligible and certificate['admissible_terminal_predecessors']==sorted(eligible) and entry['ingress_nodes']==sorted(eligible) and entry['sink']==sink and entry['budget']==budget;seen_entries=set()
   for witness in certificate['witnesses']:
    ingress=witness['ingress_node'];assert ingress in eligible and ingress not in seen_entries;seen_entries.add(ingress);u=source;seen={source};delay=0;physical=witness['physical_edge_ids'];assert physical and physical[-1]==witness['terminal_edge_id'] and us[physical[-1]]==ingress and vs[physical[-1]]==sink
    for pos,eid in enumerate(physical):
     assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and not blocked[v] and caps[v]>0
     if pos<len(physical)-1:assert types[v] not in ('SOURCE','SINK')
     seen.add(v);delay+=weights[switches[eid]];u=v
    assert u==sink and delay==witness['delay']<=budget;local_witnesses+=1;witnesses_verified+=1
   assert seen_entries==eligible;learned.append(dict(case=case,connection_id=cid,NET=net,source=source,sink=sink,budget_integer=budget,graph_sha256=sha(graph),outside_unique_NET_occupancy_sha256=stamp,conditional_budget_cut=sorted(eligible),necessity_certificate=str(certificate_path),proof_kind='EXACT_TERMINAL_INGRESS_DOMAIN_VIA_CAPPED_FORWARD_BELLMAN',scope='Necessary per-CID ownership set complete for budget-admissible terminal ingresses under exact outside occupancy. Same-NET CIDs may share ownership; not flow, parent-tree or complete routing sufficiency.'));bindings[str(certificate_path)]=sha(certificate_path);domains.append(dict(CID=cid,ingress_nodes=sorted(eligible),size=len(eligible)))
  bindings[str(path)]=sha(path);row=dict(case=case,NET=net,all_original_CIDs_covered=True,connections=len(records),min_domain_size=min(d['size'] for d in domains),max_domain_size=max(d['size'] for d in domains),terminal_domains=domains,forward_potential_edge_inequalities_verified=checked,physical_ingress_witnesses_verified=local_witnesses);rows.append(row);print('ALL_CID_EXACT_INGRESS_CERTIFICATE_PASS',json.dumps({k:v for k,v in row.items() if k!='terminal_domains'}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());artifact=D/'learned_conditional_budget_constraints_v1.json';assert not artifact.exists();artifact.write_text(json.dumps(dict(status='PROOF_BOUND_NECESSARY_CONDITIONAL_RESOURCE_AVAILABILITY_CLAUSES',clauses=learned,scope='Exact budget-admissible terminal ingress cuts for every relevant CID, assumption-bound and necessary only; no chosen NET trees or routing success.'),indent=2)+'\n');bindings[str(artifact)]=sha(artifact);(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL_RELEVANT_NET_CID_TERMINAL_INGRESS_DOMAINS_EXACTLY_CERTIFIED',rows=rows,NETs=len(rows),connections=len(learned),physical_ingress_witnesses_verified=witnesses_verified,forward_potential_edge_inequalities_verified=inequalities,bindings=bindings,scope='Independent Expat original graph replay. Forward potentials lower-bound all legal source paths; every excluded ingress edge exceeds budget by that bound, every included ingress has a physical budget witness. Entire terminal domain exact, not merely one shortest-parent support. These necessary CID cuts do not construct a complete NET tree or prove routing feasibility.'),indent=2)+'\n')
if __name__=='__main__':main()
