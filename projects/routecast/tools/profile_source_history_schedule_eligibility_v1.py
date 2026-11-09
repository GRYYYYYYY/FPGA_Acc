"""Target-label-free census on all actual complete model trajectories.
Not counterfactual execution and not native force-reroute equivalence.
"""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_source_history_trial_v1_2026-10-20';D=E/'source_history_schedule_eligibility_profile_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 decision=I/'research_decision_v1.json';v=read(decision);assert all(sha(k)==h for k,h in v['bindings'].items());protocol=read(I/'protocol.json');ep=read(protocol['cases'][0]['endpoint']);graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];D.mkdir(exist_ok=False);caps={};dest=array('Q');stack=[]
 for kind,e in ET.iterparse(graph,events=('start','end')):
  if kind=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if parent=='rr_nodes' and e.tag=='node':caps[int(e.get('id'))]=int(e.get('capacity'))
  if parent=='rr_edges' and e.tag=='edge':dest.append(int(e.get('sink_node')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(caps)==129090 and len(dest)==1312347
 def owned(records):return {q['source'] for q in records}|{dest[e] for q in records for e in q['answer']['physical_edge_ids']}
 def paths(records):return {q['connection_id']:tuple(q['answer']['physical_edge_ids']) for q in records}
 bindings={str(decision):sha(decision),str(graph):sha(graph),str(Path(__file__)):sha(__file__)};rows=[];total=0
 for c in protocol['cases']:
  assert read(c['endpoint'])['graph_sha256']==ep['graph_sha256']
  for init in ['raw_min','native_retained']:
   warm=Path(c['warm'])/init/'verification.json';dirty=set(read(warm)['dirty_nets']);bindings[str(warm)]=sha(warm)
   for arm in ['off','on']:
    out=I/c['case']/init/arm;receipt=read(out/'receipt.json');audit=read(out/'complete_event_audit.json');eventfile=out/'receipt.json';assert audit['bindings'][str(eventfile)]==sha(eventfile);assert audit['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'];seed=read(out/'initial.json');records=defaultdict(list)
    for q in seed['records']:records[q['net_id']].append(q)
    ledger=Counter({int(n):x for n,x in seed['ledger'].items()});support={n:owned(rs) for n,rs in records.items()};assert ledger==Counter(u for nodes in support.values() for u in nodes);rounds=[]
    for r in receipt['rounds']:
     round_owner={n for n,nodes in support.items() if any(ledger[u]>caps[u] for u in nodes)};counts=Counter();status=defaultdict(Counter)
     for event in r['events']:
      net=event['net_id'];old=records[net];oldnodes=support[net];over=any(ledger[u]>caps[u] for u in oldnodes);category='ENDPOINT_DIRTY' if net in dirty else 'CURRENT_OVERUSE_OWNER' if over else 'CLEAN_UNCHANGED_ENDPOINT';counts[category]+=1;counts[category+'_primary_searches']+=event['primary_search_calls'];status[category][event['status']]+=1;counts['round_start_vs_live_owner_disagreement']+=over!=(net in round_owner);total+=1
      if event['status']=='COMMITTED':
       new=event['records'];changed=paths(new)!=paths(old);counts[category+('_changed_commit' if changed else '_identical_path_commit')]+=1;newnodes=owned(new)
       for u in oldnodes-newnodes:
        ledger[u]-=1
        if not ledger[u]:del ledger[u]
       ledger.update(newnodes-oldnodes);records[net]=new;support[net]=newnodes
     frame=read(r['state_file']);assert ledger==Counter({int(n):x for n,x in frame['ledger'].items()});assert {q['connection_id']:q for rs in records.values() for q in rs}=={q['connection_id']:q for q in frame['records']};assert ledger==Counter(u for nodes in support.values() for u in nodes);assert sum(counts[k] for k in ['ENDPOINT_DIRTY','CURRENT_OVERUSE_OWNER','CLEAN_UNCHANGED_ENDPOINT'])==5919;rounds.append(dict(round_index=r['round_index'],round_start_overuse_owner_NETs=len(round_owner),endpoint_dirty_NETs=len(dirty),counts=dict(counts),status_by_category={k:dict(x) for k,x in status.items()}))
    row=dict(case=c['case'],initializer=init,arm=arm,rounds=rounds);rows.append(row)
    for p in [out/'receipt.json',out/'complete_event_audit.json',out/'initial.json',out/'round0.json',out/'round1.json']:bindings[str(p)]=sha(p)
    print('PROFILED',c['case'],init,arm,flush=True)
 assert total==142056 and all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL142056_NET_EVENTS_LIVE_CONGESTION_AND_ENDPOINT_ELIGIBILITY_CENSUS_COMPLETE',events=total,rows=rows,bindings=bindings,scope='Actual all-NET trajectories only, source/model occupancy and endpoint differences; no target labels. Classification cannot predict counterfactual live-mask trajectories or native timing/hold force flags. Full native policy equivalence not claimed.'),indent=2)+'\n')
if __name__=='__main__':main()
