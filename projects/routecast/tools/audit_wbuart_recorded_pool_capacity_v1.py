"""Label-independent necessary capacity conflicts in recorded complete-NET pools."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_recorded_pool_capacity_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_prepared_map_replication_v1_2026-10-20/manifest.json';review=source.parent/'terminal_review_v1.json';assert read(review)['events']==154656;files=[Path(__file__),source,review,R/'tools/run_MMC_aggregate_L1_oracle_v1_2026_10_19.py',R/'tools/finite_route_bank_cnf_v1.py'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_COMPLETE_NET_POOL_NECESSARY_CAPACITY_AUDIT','inputs':'Only current endpoints, original XML graph, initial/receipt complete candidates and admission proofs. No target route, truth occupancy, best-support label choices or score files read.','bound':'Each NET must select one recorded complete tree. Intersection of resource ownership over all its recorded candidates is mandatory. If more mandatory NETs than node capacity, no selection from this finite bank is capacity-feasible. This does not imply physical graph/routing impossibility or failed forecast rank for every bank choice.','prior_scope':'Archived maximum-weight closure has2-bank binary protected unit CHANNEL domain, with inherited/excluded conflicts retained. Current multivalued pools and all-node/higher capacities require separate qualification; no automatic transfer of optimality.','bindings':bindings},indent=2)+'\n');rows=[];graphs={}
 for case in read(source)['cases']:
  endpoint=Path(case['endpoint']);ep=read(endpoint);graph=ep['inputs']['graph']['path']
  if graph not in graphs:
   root=ET.parse(graph).getroot();nodes=list(root.find('rr_nodes'));graphs[graph]=([int(e.get('src_node')) for e in root.find('rr_edges')],[int(e.get('sink_node')) for e in root.find('rr_edges')],[int(n.get('capacity')) for n in nodes],[n.get('type') for n in nodes])
  src,dest,caps,kinds=graphs[graph];groups=defaultdict(set);qmeta={q['connection_id']:q for q in ep['connections']}
  for q in ep['connections']:groups[q['net_id']].add(q['connection_id'])
  for arm in read(Path(case['output'])/'verification.json')['arms']:
   for key,mode in [('control_output','H0'),('candidate_output','MAP')]:
    out=Path(arm[key]);proof=out/'complete_event_audit.json';assert read(proof)['events']==2148;initial=defaultdict(list);pool=defaultdict(set);observations=Counter()
    def offer(net,records):
     if not records or {q['connection_id'] for q in records}!=groups[net] or len(records)!=len(groups[net]):raise ValueError('incomplete NET')
     owned=set()
     for r in records:
      q=qmeta[r['connection_id']]
      if any(r[k]!=v for k,v in q.items()):raise ValueError('endpoint identity')
      u=q['source'];seen={u};owned.add(u)
      for eid in r['answer']['physical_edge_ids']:
       if src[eid]!=u:raise ValueError('arc continuity')
       u=dest[eid]
       if u in seen or caps[u]<=0:raise ValueError('cycle/disabled')
       seen.add(u);owned.add(u)
      if u!=q['sink'] or r['answer']['delay']>r['budget_integer']:raise ValueError('endpoint/budget')
     observations[net]+=1;pool[net].add(frozenset(owned))
    for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
    for net,rs in initial.items():offer(net,rs)
    for rnd in read(out/'receipt.json')['rounds']:
     for event in rnd['events']:
      rs=event.get('records',event.get('rejected_records'))
      if rs is not None:offer(event['net_id'],rs)
    mandatory=defaultdict(list);possible=defaultdict(list)
    for net,choices in pool.items():
     common=set.intersection(*(set(s) for s in choices));union=set.union(*(set(s) for s in choices))
     for n in common:mandatory[n].append(net)
     for n in union:possible[n].append(net)
    conflicts=[{'node':n,'type':kinds[n],'capacity':caps[n],'mandatory_NETs':sorted(nets)} for n,nets in sorted(mandatory.items()) if len(nets)>caps[n]];d=D/case['case']/arm['initializer']/arm['timing_policy']/mode;d.mkdir(parents=True);p=d/'necessary_conflicts.json';p.write_text(json.dumps({'conflicts':conflicts,'pool_ownership_pattern_counts':{n:len(c) for n,c in pool.items()},'candidate_observations':dict(observations)},separators=(',',':'))+'\n');row={'case':case['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'priority':mode,'output':str(out),'endpoint':str(endpoint),'payload':str(p),'NETs':len(pool),'ownership_patterns':sum(map(len,pool.values())),'pool_size_histogram':dict(Counter(map(len,pool.values()))),'mandatory_overcapacity_nodes':len(conflicts),'mandatory_overcapacity_CHANNELs':sum(c['type'] in ['CHANX','CHANY'] for c in conflicts),'mandatory_overflow_unit_lower_bound':sum(len(c['mandatory_NETs'])-c['capacity'] for c in conflicts),'possible_contention_nodes':sum(len(nets)>caps[n] for n,nets in possible.items()),'result':'FINITE_BANK_FULL_CAPACITY_INFEASIBLE_WITNESS' if conflicts else 'NO_MANDATORY_CONFLICT_NOT_A_FEASIBILITY_PROOF'};rows.append(row);print(case['case'],arm['initializer'],arm['timing_policy'],mode,row['mandatory_overcapacity_nodes'],flush=True)
    for p in [p,proof,out/'initial.json',out/'receipt.json',endpoint,Path(graph)]:bindings[str(p)]=sha(p)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_RECORDED_POOL_MANDATORY_OWNERSHIP_CAPACITY_BOUNDS_COMPUTED','rows':rows,'bindings':bindings,'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
