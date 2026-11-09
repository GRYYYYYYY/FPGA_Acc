"""Independent inverse-owner sets, full old-tree release/new-tree install replay."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_source_history_trial_v1_2026-10-20';D=E/'source_history_schedule_eligibility_profile_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=D/'verification.json';p=read(proof);assert all(sha(k)==h for k,h in p['bindings'].items());protocol=read(I/'protocol.json');graph=Path(read(protocol['cases'][0]['endpoint'])['inputs']['graph']['path']);capacities={};targets=[]
 for _,el in ET.iterparse(graph):
  if el.tag=='node' and el.get('capacity') is not None:capacities[int(el.get('id'))]=int(el.get('capacity'))
  if el.tag=='edge' and el.get('sink_node') is not None:targets.append(int(el.get('sink_node')))
  el.clear()
 def nodes(rs):
  result=set()
  for q in rs:
   result.add(q['source'])
   for edge in q['answer']['physical_edge_ids']:result.add(targets[edge])
  return result
 rows=[];checked=0
 for observed in p['rows']:
  case=next(c for c in protocol['cases'] if c['case']==observed['case']);folder=I/case['case']/observed['initializer']/observed['arm'];seed=read(folder/'initial.json');records=defaultdict(list)
  for q in seed['records']:records[q['net_id']].append(q)
  inverse=defaultdict(set)
  for net,rs in records.items():
   for node in nodes(rs):inverse[node].add(net)
  dirty=set(read(Path(case['warm'])/observed['initializer']/'verification.json')['dirty_nets']);receipt=read(folder/'receipt.json')
  for r,expected in zip(receipt['rounds'],observed['rounds']):
   beginning=set()
   for node,owners in inverse.items():
    if len(owners)>capacities[node]:beginning.update(owners)
   assert len(beginning)==expected['round_start_overuse_owner_NETs'];counts=Counter();statuses=defaultdict(Counter)
   for event in r['events']:
    net=event['net_id'];old=records[net];occupied=nodes(old);over=any(len(inverse[n])>capacities[n] for n in occupied);category='ENDPOINT_DIRTY' if net in dirty else 'CURRENT_OVERUSE_OWNER' if over else 'CLEAN_UNCHANGED_ENDPOINT';counts[category]+=1;counts[category+'_primary_searches']+=event['primary_search_calls'];statuses[category][event['status']]+=1;counts['round_start_vs_live_owner_disagreement']+=over!=(net in beginning);checked+=1
    if event['status']=='COMMITTED':
     new=event['records'];a=sorted((x['connection_id'],x['answer']['physical_edge_ids']) for x in old);b=sorted((x['connection_id'],x['answer']['physical_edge_ids']) for x in new);counts[category+('_changed_commit' if a!=b else '_identical_path_commit')]+=1
     for node in occupied:
      assert net in inverse[node];inverse[node].remove(net)
     for node in nodes(new):inverse[node].add(net)
     records[net]=new
   assert dict(counts)==expected['counts'];assert {k:dict(v) for k,v in statuses.items()}==expected['status_by_category'];frame=read(r['state_file']);actual={n:len(v) for n,v in inverse.items() if v};assert actual=={int(n):v for n,v in frame['ledger'].items()};assert {x['connection_id']:x for rs in records.values() for x in rs}=={x['connection_id']:x for x in frame['records']}
  rows.append(dict(case=observed['case'],initializer=observed['initializer'],arm=observed['arm'],all_live_categories_inverse_owner_verified=True))
 assert checked==142056 and all(sha(k)==h for k,h in p['bindings'].items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL142056_LIVE_ELIGIBILITY_CATEGORIES_INDEPENDENT_INVERSE_OWNER_PASS',events=checked,rows=rows,bindings={str(proof):sha(proof),str(Path(__file__)):sha(__file__)},scope='Classification on observed all-NET trajectories only. No counterfactual outcome, native timing-force equivalence or new quality admission.'),indent=2)+'\n');print('ALL142056_LIVE_ELIGIBILITY_CATEGORIES_INDEPENDENT_INVERSE_OWNER_PASS')
if __name__=='__main__':main()
