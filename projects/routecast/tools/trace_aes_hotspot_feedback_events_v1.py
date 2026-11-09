import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_feedback_round_ablation_v1_2026-10-08';p=out/'NET_owner_diagnosis.json';d=json.loads(p.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};rows=[]
for row in d['rows']:
 name=row['name'];epfile=R/'experiments/aes_native_demand_frontend_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(epfile.read_text());byname={v:int(k) for k,v in ep['net_names'].items()};resident=R/'experiments/aes_native_demand_estimates_v1_2026-10-08'/name/'resident';rp=resident/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(k)==v for k,v in receipt['bindings'].items());assert all(sha(k)==v for k,v in receipt['files'].items());bindings[str(rp)]=sha(rp);bindings[str(epfile)]=sha(epfile)
 frames={}
 for frame in ['initial','round0','round1']:
  f=resident/(frame+'.json');state=json.loads(f.read_text());frames[frame]={r['connection_id']:r for r in state['records']};bindings[str(f)]=sha(f)
 traces=[]
 for g in row['repeated_support_group_NETs']:
  nets=set(g['native_NETs'])|{n for s in g['frames'].values() for n in s['predicted_NETs']};nodes=set(g['physical_nodes']);owners={n['node']:n for n in row['all_top20_node_owners'] if n['node'] in nodes}
  for net in sorted(nets):
   qs=[q for q in ep['connections'] if q['net_id']==byname[net]];assert qs;events=[]
   for i,r in enumerate(receipt['rounds']):
    ev=[e for e in r['events'] if e['net_id']==byname[net]];assert len(ev)<=1
    before=frames['initial' if i==0 else 'round0'];after=frames['round0' if i==0 else 'round1'];old=[before[q['connection_id']] for q in qs];new=[after[q['connection_id']] for q in qs]
    if not ev:assert old==new;status='UNAFFECTED'
    else:
     status=ev[0]['status']
     if status=='COMMITTED':assert ev[0]['records']==new and ev[0]['new_epoch']==ev[0]['old_epoch']+1
     else:assert status=='RETAIN_BUDGET_OR_UNREACHABLE' and old==new and ev[0]['new_epoch']==ev[0]['old_epoch']
    events.append(dict(round_index=i,status=status,changed_connection_paths=sum(a['answer']['physical_edge_ids']!=b['answer']['physical_edge_ids'] for a,b in zip(old,new))))
   usage={frame:sorted(n for n,owner in owners.items() if net in owner['frames'][frame]['predicted_owners']) for frame in frames}
   traces.append(dict(name=net,native_group_owner=net in g['native_NETs'],physical_connections=len(qs),group_nodes_by_state=usage,feedback_events=events))
 rows.append(dict(name=name,traces=traces))
assert all(sha(k)==v for k,v in bindings.items())
(out/'hotspot_feedback_event_trace.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Retrospective full event/frame linkage for all NETs using repeated true-hotspot support in native or any predicted state. Exact failed-retention and committed-event checks; no native timing-objective causation claim.'),indent=2)+'\n')
for r in rows:
 for t in r['traces']:
  if t['native_group_owner']:print(t['name'],t['physical_connections'],{k:len(v) for k,v in t['group_nodes_by_state'].items()},t['feedback_events'])
