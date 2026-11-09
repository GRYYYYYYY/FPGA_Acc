"""Diagnostic-only exact cold target path versus frozen forecast raw budgets."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from zero_rc_budget_certificate_graph_v1 import load_graph
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';A=E/'prospective_external_family_capacity_retry_v1_2026-10-20';D=E/'prospective_external_family_target_budget_compatibility_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 decision=read(A/'research_decision_v1.json');assert all(sha(p)==h for p,h in decision['bindings'].items());cases=read(A/'protocol.json')['cases'];graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);D.mkdir(exist_ok=False);bindings={str(A/'research_decision_v1.json'):sha(A/'research_decision_v1.json'),str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__)}
 (D/'protocol.json').write_text(json.dumps(dict(cases=[c['case'] for c in cases],policy='ALL3 all15616 CIDs, same raw/native warm budgets and floors, exact original zero-RC XML switch delays at scale1e18. Bind native paths by NET name+SOURCE+SINK with multiplicity and ambiguity checks. Labels diagnostic only, no budget relaxation/relabeling/prediction, no inference of aggregate forecast impossibility.'),indent=2)+'\n')
 g=load_graph(graph);arcs=set(zip(g['us'],g['vs'],g['switches']));rows=[]
 for c in cases:
  case=c['case'];ep=read(Path(c['endpoint']));warm_path=Path(c['warm'])/'native_retained/initial.json';warm=read(warm_path);raw_path=Path(c['warm'])/'raw_min/initial.json';raw=read(raw_path);assert warm['scale']==raw['scale']==10**18;old=read(Path(c['source_frame']));prior={q['connection_id']:q for q in old['records']};byid={q['connection_id']:q for q in warm['records']};rawbyid={q['connection_id']:q for q in raw['records']};assert byid.keys()==rawbyid.keys();assert all((byid[cid]['floor_integer'],byid[cid]['budget_integer'])==(rawbyid[cid]['floor_integer'],rawbyid[cid]['budget_integer']) for cid in byid);expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);route=Path(c['label_physical_audit']).parent/'output.route';paths=physical_paths(route);observed=Counter();lookup={}
  for name,pp in paths.items():
   for path in pp:
    key=name,path[0][0],path[-1][0];observed[key]+=1
    if key in lookup:assert lookup[key]==path,'ambiguous repeated SINK paths'
    lookup[key]=path
  assert expected==observed
  netcategories={};rank={'endpoint_unchanged':0,'sink_only':1,'source_moved':2}
  for q in ep['connections']:
   cid=q['connection_id'];n=q['net_id'];a=prior[cid];category='source_moved' if q['source']!=a['source'] else 'sink_only' if q['sink']!=a['sink'] else 'endpoint_unchanged'
   if rank[category]>rank.get(netcategories.get(n),-1):netcategories[n]=category
  details=[];percat={k:Counter() for k in rank};netviolations=defaultdict(set)
  for q in ep['connections']:
   cid=q['connection_id'];record=byid[cid];assert all(record[k]==v for k,v in q.items());path=lookup[ep['net_names'][str(q['net_id'])],q['source'],q['sink']];value=0;seen={path[0][0]}
   for (u,_),(v,switch) in zip(path,path[1:]):assert (u,v,switch) in arcs and v not in seen;seen.add(v);value+=g['weights'][switch]
   floor=record['floor_integer'];budget=record['budget_integer'];assert value>=floor and budget>=floor;category=netcategories[q['net_id']];bad=value>budget;s=percat[category];s['connections']+=1;s['violations']+=bad;s['total_excess']+=max(0,value-budget)
   if bad:netviolations[category].add(q['net_id'])
   details.append(dict(connection_id=cid,net_id=q['net_id'],source=q['source'],sink=q['sink'],category=category,target_delay_integer=value,budget_integer=budget,floor_integer=floor,excess_integer=max(0,value-budget),violation=bad,hops=len(path)-1))
  for cat in percat:percat[cat]['NETs_with_violation']=len(netviolations[cat])
  out=D/case;out.mkdir(parents=True);payload=out/'connections.json';payload.write_text(json.dumps(details)+'\n');count=sum(x['violation'] for x in details);row=dict(case=case,connections=len(details),violations=count,NETs_with_violation=sum(len(x) for x in netviolations.values()),max_excess_integer=max(x['excess_integer'] for x in details),categories={k:dict(v) for k,v in percat.items()});rows.append(row);print(json.dumps(row),flush=True)
  for p in [warm_path,raw_path,Path(c['source_frame']),Path(c['endpoint']),Path(c['label_proof']),route,payload]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_COLD_TARGET_CID_BINDINGS_AND_EXACT_RAW_BUDGET_COMPATIBILITY_AUDITED',rows=rows,bindings=bindings,scale=10**18,scope='Individual target path compatibility only. Other paths can produce the same aggregate demand; violations are not proof that forecast metrics are unattainable. No thresholds or labels changed.'),indent=2)+'\n')
if __name__=='__main__':main()
