"""Reconstruct initial frame from cached native clean records and dirty payload."""
import json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from retained_native_warm_checkpoint_v2 import Checkpoint as Original

class Checkpoint(Original):
 def __init__(self,session,initial,proof):
  super().__init__(session,initial,proof)
  self.source_initial=str(Path(initial).resolve());self.source_hash=self.bindings[self.source_initial]
 def from_recipe(self,path,dirty):
  path=Path(path).resolve();proof_path=path.with_suffix('.proof.json');proof=json.loads(proof_path.read_text())
  if proof.get('recipe')!=str(path) or proof['bindings'].get(str(path))!=sha(path):raise ValueError('unbound dirty recipe')
  if not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('dirty recipe dependency changed')
  payload=json.loads(path.read_text());result=self._build(payload,dirty)
  return result,{**proof['bindings'],str(proof_path):sha(proof_path)}
 def _build(self,payload,declared_dirty):
  s=self.session
  if s.closed or not s.active or s.owner is not self.owner or s.owner.state is not self.state or s.owner.generation!=self.generation:raise RuntimeError('stale native checkpoint generation')
  if payload.get('schema')!='NATIVE_DIRTY_TRANSITION_RECIPE_V1' or payload['source_initial']!=self.source_initial or payload['source_initial_sha256']!=self.source_hash:raise ValueError('dirty recipe source checkpoint mismatch')
  if s.digest!=self.graph_digest or s.rc.scale!=self.scale:raise ValueError('graph/RC epoch changed')
  if set(s.current_queries)!=set(self.records):raise ValueError('CID domain changed')
  dirty={q['net_id'] for cid,q in s.current_queries.items() if (q['source'],q['sink'])!=(self.state.queries[cid]['source'],self.state.queries[cid]['sink'])}
  if dirty!=set(declared_dirty) or dirty!=set(payload['dirty_nets']):raise ValueError('dirty closure mismatch')
  updates={}
  for record in payload['dirty_records']:
   cid=record['connection_id']
   if cid in updates or cid not in s.current_queries or s.current_queries[cid]['net_id'] not in dirty:raise ValueError('invalid dirty CID')
   updates[cid]=record
  if set(updates)!={cid for cid,q in s.current_queries.items() if q['net_id'] in dirty}:raise ValueError('incomplete dirty CID coverage')
  records=[];unions=defaultdict(set);independent=Counter();f=s.fields;slots={eid:i for i,eid in enumerate(f['edge_ids'])}
  for cid in self.records:
   q=s.current_queries[cid];record=json.loads(json.dumps(updates[cid])) if cid in updates else json.loads(self.records[cid])
   if (record['net_id'],record['source'],record['sink'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('recipe endpoint mismatch')
   nodes={q['source']}|{f['dest_ranks'][slots[eid]] for eid in record['answer']['physical_edge_ids']}
   records.append(record);unions[q['net_id']].update(nodes);independent.update(nodes)
  ledger=Counter(n for nodes in unions.values() for n in nodes)
  values=dict(payload['metadata']);values.update(records=records,ledger={str(n):v for n,v in ledger.items()},independent_connection_ledger={str(n):v for n,v in independent.items()},epochs={str(n):v+int(n in dirty) for n,v in self.epochs.items()},overflow_units=sum(max(0,v-f['capacities'][n]) for n,v in ledger.items()))
  for key,order in payload['key_orders'].items():
   if key not in ('ledger','independent_connection_ledger','epochs') or len(order)!=len(set(order)) or set(order)!=set(values[key]):raise ValueError('invalid serialization key domain')
   values[key]={n:values[key][n] for n in order}
  order=payload['top_key_order']
  if len(order)!=len(set(order)) or set(order)!=set(values):raise ValueError('invalid top key domain')
  result={k:values[k] for k in order}
  digest=hashlib.sha256((json.dumps(result)+'\n').encode()).hexdigest()
  if digest!=payload['expected_initial_sha256']:raise ValueError('reconstructed initial digest mismatch')
  return result
