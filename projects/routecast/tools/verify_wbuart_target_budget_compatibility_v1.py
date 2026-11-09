"""Parent-pointer route parser and independent XML Fraction electrical context."""
import json,sys,hashlib
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from audit_native_route import NET,NODE
from independent_fraction_arc_context_v2 import load_context,arc_delay
E=R/'experiments';D=E/'wbuart_native_target_budget_diagnosis_v1_2026-10-20';A=E/'prospective_external_family_capacity_retry_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(D/'verification.json');assert all(sha(p)==h for p,h in proof['bindings'].items());cases=proof['rows'];rows=[]
 for c in cases:
  case=c['case'];ep=read(Path(c['endpoint']));graph=Path(ep['inputs']['graph']['path']);xml,ids,classes,switches,digest=load_context(graph,sha(graph));assert all(r==cap==0 for r,cap in classes) and all(r==0 for r,t in switches.values());warm=read(Path(c['warm_directory'])/'initial.json');scale=warm['scale'];expected={q['connection_id']:q for q in ep['connections']};stored={q['connection_id']:q for q in read(D/case/'connections.json')};assert set(stored)==set(expected);parents={};current=None;previous=None;previous_switch=None;paths=defaultdict(list);observed=Counter();route=Path(c['native_route'])
  for line in route.read_text().splitlines():
   m=NET.match(line)
   if m:current=m[2];parents={};previous=None;previous_switch=None
   m=NODE.match(line)
   if not m:continue
   node=int(m[1]);kind=m[2]
   if kind=='SOURCE':assert not parents;parents[node]=None
   elif kind=='SINK':
    chain=[(previous,node,previous_switch)];u=previous;seen={node,u}
    while parents[u] is not None:
     parent,switch=parents[u];chain.append((parent,u,switch));u=parent;assert u not in seen;seen.add(u)
    chain.reverse();key=current,u,node;value=Fraction(0)
    for src,dst,switch in chain:
     assert any(e.sink==dst and e.switch_id==switch for e in xml.graph.edges[xml.graph.row_offsets[src]:xml.graph.row_offsets[src+1]]) if hasattr(xml.graph,'row_offsets') else True
     value+=arc_delay(classes,switches,ids[dst],switch)
    paths[key].append(value);observed[key]+=1
   elif node not in parents:
    assert previous in parents;parents[node]=previous,previous_switch
   previous=node;previous_switch=int(m[3])
  queries=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in expected.values());assert queries==observed
  prior={q['connection_id']:q for q in read(Path(c['source_frame']))['records']};cats={};rank={'endpoint_unchanged':0,'sink_only':1,'source_moved':2};warmrows={q['connection_id']:q for q in warm['records']}
  for cid,q in expected.items():
   old=prior[cid];category='source_moved' if old['source']!=q['source'] else 'sink_only' if old['sink']!=q['sink'] else 'endpoint_unchanged'
   if rank[category]>rank.get(cats.get(q['net_id']),-1):cats[q['net_id']]=category
  violations=0;percat=defaultdict(Counter);netbad=defaultdict(set)
  for cid,q in expected.items():
   key=ep['net_names'][str(q['net_id'])],q['source'],q['sink'];values=paths[key];assert len(set(values))==1;integer=values[0]*scale;assert integer.denominator==1;value=integer.numerator;s=stored[cid];budget=warmrows[cid]['budget_integer'];floor=warmrows[cid]['floor_integer'];assert s['target_delay_integer']==value and s['budget_integer']==budget and s['floor_integer']==floor and value>=floor;bad=value>budget;assert s['violation']==bad and s['excess_integer']==max(0,value-budget) and s['category']==cats[q['net_id']];violations+=bad;cat=cats[q['net_id']];percat[cat]['connections']+=1;percat[cat]['violations']+=bad;percat[cat]['total_excess']+=max(0,value-budget)
   if bad:netbad[cat].add(q['net_id'])
  summary=next(q for q in proof['rows'] if q['case']==case);assert summary['violations']==violations
  for cat in rank:percat[cat]['NETs_with_violation']=len(netbad[cat]);assert dict(percat[cat])==summary['categories'][cat]
  rows.append(dict(case=case,connections=len(expected),violations=violations,parent_pointer_paths_and_original_XML_fraction_delays_exact=True));print(rows[-1],flush=True)
 assert len(rows)==9 and sum(r['connections'] for r in rows)==22437
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL22437_TARGET_CID_BUDGET_COMPARISONS_INDEPENDENT_FRACTION_AND_ROUTE_PARENT_POINTER_PASS',rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Independent electrical arithmetic and route representation. No aggregate forecast infeasibility claim.'),indent=2)+'\n')
if __name__=='__main__':main()
