"""Input-only factor scopes and symbolic deterministic min-fill complexity."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from math import prod
from symbolic_NET_elimination_v1 import plan
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_candidate_elimination_profile_v1_2026-10-20'
def read(p):
 p=Path(p)
 if any(x in p.parts for x in ['cold','utility','specifications']) or 'label' in p.name or 'comparison' in p.name:raise ValueError('target/score input forbidden')
 return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_prepared_map_replication_v1_2026-10-20/manifest.json';contract=E/'symbolic_NET_elimination_contract_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());files=[Path(__file__),source,contract,R/'tools/symbolic_NET_elimination_v1.py'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_INPUT_ONLY_SYMBOLIC_MINFILL_PROFILE','factors':'For each positive-capacity CHANNEL, variable scope is NETs whose recorded candidate membership varies; fixed NET contributions are constants. Combine identical scopes structurally, omit one-state variables with certificate. No numerical target/factor values read.','order':'Greedy min-fill, then bag assignment count, then degree, then NET ID. Exact integer state-cardinality products. This is not a minimum-treewidth algorithm.','scope':'Profile all72 admitted input banks without actual message allocation/inference/quality evaluation. Dense payload byte estimates exclude Python/container metadata, live factor scheduling and complete workflow. Do not infer runtime or speedup from state counts.','bindings':bindings},indent=2)+'\n');graphs={};rows=[]
 for case in read(source)['cases']:
  ep=Path(case['endpoint']);meta=read(ep);graph=meta['inputs']['graph']['path']
  if graph not in graphs:
   root=ET.parse(graph).getroot();graphs[graph]=([int(e.get('sink_node')) for e in root.find('rr_edges')],{int(n.get('id')) for n in root.find('rr_nodes') if n.get('type') in ['CHANX','CHANY'] and int(n.get('capacity'))>0})
  dest,channels=graphs[graph]
  for arm in read(Path(case['output'])/'verification.json')['arms']:
   for key,mode in [('control_output','H0'),('candidate_output','MAP')]:
    out=Path(arm[key]);initial=defaultdict(list);pools=defaultdict(set)
    def add(net,rs):pools[net].add(frozenset(dest[e] for q in rs for e in q['answer']['physical_edge_ids'] if dest[e] in channels))
    for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
    for n,rs in initial.items():add(n,rs)
    for rnd in read(out/'receipt.json')['rounds']:
     for event in rnd['events']:
      rs=event.get('records',event.get('rejected_records'))
      if rs is not None:add(event['net_id'],rs)
    cards={n:len(cs) for n,cs in pools.items()};users=defaultdict(list)
    for net,choices in pools.items():
     variable=set.union(*(set(c) for c in choices))-set.intersection(*(set(c) for c in choices))
     for n in variable:users[n].append(net)
    scopes=defaultdict(list)
    for n in sorted(channels):scopes[tuple(sorted(users[n]))].append(n)
    scope_rows=[{'NETs':list(s),'CHANNELs':nodes,'states':prod(cards[n] for n in s)} for s,nodes in sorted(scopes.items())];answer=plan(cards,scopes);d=D/case['case']/arm['initializer']/arm['timing_policy']/mode;d.mkdir(parents=True);p=d/'symbolic_plan.json';p.write_text(json.dumps({'cardinalities':cards,'resource_factor_scopes':scope_rows,**answer},separators=(',',':'))+'\n');row={'case':case['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'priority':mode,'endpoint':str(ep),'output':str(out),'payload':str(p),'NETs':len(cards),'variable_NETs':len(answer['steps']),'induced_width':answer['induced_width'],'largest_initial_factor_states':max(r['states'] for r in scope_rows),'largest_bag_states':answer['largest_bag_states'],'largest_separator_states':answer['largest_separator_states'],'sum_bag_states':answer['sum_bag_states'],'sum_separator_states':answer['sum_separator_states'],'largest_64bit_cost_plus_argmin_payload_bytes':16*answer['largest_separator_states'],'all_backpointer_64bit_payload_bytes':8*answer['sum_separator_states']};rows.append(row);print(case['case'],arm['initializer'],arm['timing_policy'],mode,row['induced_width'],row['largest_bag_states'],row['sum_bag_states'],flush=True)
    for path in [p,ep,Path(graph),out/'initial.json',out/'receipt.json']:bindings[str(path)]=sha(path)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_INPUT_ONLY_SYMBOLIC_ELIMINATION_PROFILES_COMPUTED','rows':rows,'bindings':bindings,'target_payloads_read':False,'numeric_solver_executed':False,'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
