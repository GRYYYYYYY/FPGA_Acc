"""Diagnostic-only target whole-NET admissibility at one fixed original warm state."""
import json,sys,hashlib,xml.etree.ElementTree as ET
from array import array
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from zero_rc_budget_certificate_graph_v1 import load_graph
from native_route_ledger_import_compact import physical_paths
from criticality_objective_admission_v1 import score
E=R/'experiments';A=E/'prospective_external_family_capacity_retry_v1_2026-10-20';B=E/'prospective_external_family_target_budget_compatibility_v1_2026-10-20';M=E/'prospective_external_family_fixed_nominal_NET_error_v1_2026-10-19';D=E/'prospective_external_family_target_NET_constraints_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(B/'research_decision_v1.json');assert all(sha(p)==h for p,h in proof['bindings'].items());cases=read(A/'protocol.json')['cases'];graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);D.mkdir(exist_ok=False);g=load_graph(graph);arcs={}
 for eid,(u,v,s) in enumerate(zip(g['us'],g['vs'],g['switches'])):
  key=u,v,s;assert key not in arcs,'ambiguous RR arc';arcs[key]=eid
 fields=dict(dest_ranks=g['vs']);slots={i:i for i in range(len(g['vs']))};spans={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes' and e.get('type') in ('CHANX','CHANY'):
   loc=e.find('loc');spans[int(e.get('id'))]=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 bindings={str(graph):sha(graph),str(B/'research_decision_v1.json'):sha(B/'research_decision_v1.json'),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/criticality_objective_admission_v1.py'):sha(R/'tools/criticality_objective_admission_v1.py')};(D/'protocol.json').write_text(json.dumps(dict(cases=[c['case'] for c in cases],snapshot='Original native_retained warm, before round0; zero history, fixed warm-derived criticality, owner-excluded original multiplicative base+static span cost',policy='All target NETs diagnostic only. Report independent budget/pressure/objective flags and hierarchical budget then pressure then objective exclusion. No label input to producer or actual commits; no thresholds changed.'),indent=2)+'\n');results=[]
 def owned(recs):return {r['source'] for r in recs}|{g['vs'][eid] for r in recs for eid in r['answer']['physical_edge_ids']}
 for c in cases:
  case=c['case'];ep=read(Path(c['endpoint']));wp=Path(c['warm'])/'native_retained/initial.json';warm=read(wp);assert warm['scale']==10**18 and read(Path(c['warm'])/'native_retained/history.json')=={};ledger={int(n):v for n,v in warm['ledger'].items()};weight=warm['scale']//(20*10**9);budgetrows={q['connection_id']:q for q in read(B/case/'connections.json')};oldbyid={q['connection_id']:q for q in warm['records']};old=defaultdict(list);target=defaultdict(list);critfile=A/case/'off/timing_round0.json';crit={q['connection_id']:q for q in read(critfile)['criticalities']};bp=Path(c['node_base_proof']);basefile=bp.parent/'node_base.u64';baseproof=read(bp);assert baseproof['bindings'][str(basefile)]==sha(basefile);base=array('Q');base.frombytes(basefile.read_bytes());assert len(base)==len(g['caps']);meta={q['net_id']:q for q in read(M/case/'per_NET.json')};route=Path(c['label_physical_audit']).parent/'output.route';lookup={}
  for name,pp in physical_paths(route).items():
   for path in pp:
    key=name,path[0][0],path[-1][0]
    if key in lookup:assert lookup[key]==path
    lookup[key]=path
  for q in ep['connections']:
   cid=q['connection_id'];record=oldbyid[cid];n=q['net_id'];old[n].append(record);path=lookup[ep['net_names'][str(n)],q['source'],q['sink']];edges=[arcs[u,v,s] for (u,_),(v,s) in zip(path,path[1:])];value=sum(g['weights'][g['switches'][eid]] for eid in edges);assert value==budgetrows[cid]['target_delay_integer'];target[n].append(dict(record,answer=dict(status='FOUND',physical_edge_ids=edges,delay=value)))
  assert dict(Counter(n for recs in old.values() for n in owned(recs)))==ledger
  targetledger=Counter(n for recs in target.values() for n in owned(recs));assert dict(targetledger)=={int(n):v for n,v in read(Path(c['label_physical_audit']))['node_occupancy'].items()};details=[];summary={name:Counter() for name in ('all_NETs','target_changing_clean_NETs')}
  for n in sorted(old):
   before=owned(old[n]);after=owned(target[n]);updates={u:ledger.get(u,0)-1 for u in before-after};updates.update({u:ledger.get(u,0)+1 for u in after-before});pressure=sum(max(0,value-g['caps'][u])-max(0,ledger.get(u,0)-g['caps'][u]) for u,value in updates.items());bad=[q['connection_id'] for q in target[n] if q['answer']['delay']>q['budget_integer']]
   class Prices:
    def get(self,node,default=0):return base[node]*(1+max(0,ledger.get(node,0)-(node in before)-g['caps'][node]+1))+weight*spans.get(node,0)
   prices=Prices();before_score=score(fields,slots,old[n],crit,prices,{q['connection_id']:q['answer']['delay'] for q in old[n]});after_score=score(fields,slots,target[n],crit,prices,{q['connection_id']:q['answer']['delay'] for q in target[n]});delta=after_score-before_score;category='budget' if bad else 'pressure' if pressure>0 else 'objective' if delta>0 else 'admissible';cohort=meta[n]['category']=='endpoint_unchanged' and meta[n]['target_changed_from_source'];details.append(dict(net_id=n,endpoint_category=meta[n]['category'],target_changing_clean=cohort,budget_violating_CIDs=bad,pressure_delta=pressure,old_score=str(before_score),target_score=str(after_score),objective_delta=str(delta),hierarchical_exclusion=category))
   for which in (['all_NETs','target_changing_clean_NETs'] if cohort else ['all_NETs']):
    s=summary[which];s['NETs']+=1;s['budget_fail']+=bool(bad);s['pressure_fail']+=pressure>0;s['objective_fail']+=delta>0;s['hierarchical_'+category]+=1
  out=D/case;out.mkdir(parents=True);detailsfile=out/'NET_constraints.json';detailsfile.write_text(json.dumps(details)+'\n');targetfile=out/'target_records.json';targetfile.write_text(json.dumps([q for recs in target.values() for q in recs])+'\n');row=dict(case=case,summary={k:dict(v) for k,v in summary.items()});results.append(row);print(json.dumps(row),flush=True)
  for p in [wp,critfile,bp,basefile,route,Path(c['endpoint']),B/case/'connections.json',M/case/'per_NET.json',detailsfile,targetfile]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_FROZEN_WARM_TARGET_NET_BUDGET_PRESSURE_AND_OBJECTIVE_CLASSIFICATION_COMPLETE',rows=results,bindings=bindings,scope='Single snapshot diagnostic. Independent flags can overlap; hierarchy gives disjoint first exclusions. Native target is globally legal but perNET insertion into warm can raise pressure. Does not establish reachability via alternate global sequences or aggregate forecast impossibility.'),indent=2)+'\n')
if __name__=='__main__':main()
