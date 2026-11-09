"""Certified native record cache bound to an exact retained owner generation."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha

class Checkpoint:
 def __init__(self,session,initial_path,proof_path):
  if session.active or session.closed or session.owner is None:raise RuntimeError('checkpoint lifecycle')
  initial_path=Path(initial_path).resolve();proof_path=Path(proof_path).resolve()
  proof=json.loads(proof_path.read_text())
  if not (proof.get('all_native_paths_exact') and proof.get('all_native_delays_and_budgets_exact') and proof.get('all_uniqueNET_occupancy_matches_full_printed_audit')):raise ValueError('native checkpoint certificate required')
  if proof['bindings'].get(str(initial_path))!=sha(initial_path) or not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('checkpoint binding changed')
  frame=json.loads(initial_path.read_text());state=session.owner.state
  if frame['scale']!=session.rc.scale:raise ValueError('checkpoint RC scale')
  slots={eid:e for e,eid in enumerate(session.fields['edge_ids'])};records={}
  for record in frame['records']:
   cid=record['connection_id']
   if cid in records or cid not in state.paths:raise ValueError('checkpoint CID coverage')
   q=state.queries[cid]
   if (record['net_id'],record['source'],record['sink'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('checkpoint endpoint')
   path=[(q['source'],None)];u=q['source']
   for eid in record['answer']['physical_edge_ids']:
    slot=slots[eid]
    if not session.fields['row_offsets'][u]<=slot<session.fields['row_offsets'][u+1]:raise ValueError('checkpoint arc source')
    u=session.fields['dest_ranks'][slot];path.append((u,session.fields['switch_ids'][slot]))
   if tuple(path)!=state.paths[cid]:raise ValueError('checkpoint differs from retained native path')
   if session.rc.path(q['source'],q['sink'],record['answer']['physical_edge_ids'])!=record['answer']['delay']:raise ValueError('checkpoint RC delay')
   if record['answer']['delay']>record['budget_integer']:raise ValueError('checkpoint native anchor budget')
   records[cid]=json.dumps(record)
  if set(records)!=set(state.paths):raise ValueError('checkpoint incomplete')
  self.session=session;self.owner=session.owner;self.state=state;self.generation=session.owner.generation
  self.graph_digest=session.digest;self.scale=session.rc.scale;self.records=records
  self.epochs={int(n):v for n,v in frame['epochs'].items()}
  self.bindings={**proof['bindings'],str(proof_path):sha(proof_path)}
 def reconstruct(self,template,declared_dirty):
  s=self.session
  if s.closed or not s.active or s.owner is not self.owner or s.owner.generation!=self.generation or s.owner.state is not self.state:raise RuntimeError('stale native checkpoint generation')
  if s.digest!=self.graph_digest or s.rc.scale!=self.scale:raise ValueError('checkpoint graph/RC changed')
  if set(s.current_queries)!=set(self.records):raise ValueError('checkpoint CID domain changed')
  dirty={q['net_id'] for cid,q in s.current_queries.items() if (q['source'],q['sink'])!=(self.state.queries[cid]['source'],self.state.queries[cid]['sink'])}
  if dirty!=set(declared_dirty):raise ValueError('dirty closure differs from checkpoint endpoints')
  records=[];seen=set();unions=defaultdict(set);independent=Counter();f=s.fields;slots={eid:e for e,eid in enumerate(f['edge_ids'])}
  for supplied in template['records']:
   cid=supplied['connection_id']
   if cid in seen or cid not in self.records:raise ValueError('warm CID coverage')
   seen.add(cid);q=s.current_queries[cid]
   record=json.loads(self.records[cid]) if q['net_id'] not in dirty else json.loads(json.dumps(supplied))
   if (record['net_id'],record['source'],record['sink'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('warm endpoint')
   nodes={q['source']}|{f['dest_ranks'][slots[eid]] for eid in record['answer']['physical_edge_ids']}
   unions[q['net_id']].update(nodes);independent.update(nodes);records.append(record)
  if seen!=set(self.records):raise ValueError('warm incomplete')
  ledger=Counter(n for nodes in unions.values() for n in nodes)
  result=json.loads(json.dumps(template));result['records']=records
  result['ledger']={str(n):v for n,v in ledger.items()};result['independent_connection_ledger']={str(n):v for n,v in independent.items()}
  result['epochs']={str(n):v+int(n in dirty) for n,v in self.epochs.items()}
  result['overflow_units']=sum(max(0,v-f['capacities'][n]) for n,v in ledger.items())
  if result!=template:raise ValueError('retained native reconstruction differs from certified warm fixture')
  # Preserve the certified serialization order after full reconstructed value
  # equality. Values below come exclusively from the rebuilt counters/epochs.
  for key in ('ledger','independent_connection_ledger','epochs'):
   computed=result[key]
   result[key]={n:computed[n] for n in template[key]}
  return result
