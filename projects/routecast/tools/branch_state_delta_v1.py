"""Lossless JSON-normalized branch archive; no routing decisions or omitted states."""
import copy,json,hashlib
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def pack(seed,state):
 before={r['connection_id']:r for r in seed['records']};after={r['connection_id']:r for r in state['records']}
 if len(before)!=len(seed['records']) or len(after)!=len(state['records']):raise ValueError('duplicate record identities')
 if not set(before)<=set(after) or any(after[cid]!=r for cid,r in before.items()):raise ValueError('retained seed changed')
 ledger=seed['ledger'];updates={n:v for n,v in state['ledger'].items() if ledger.get(n)!=v};removed=[n for n in ledger if n not in state['ledger']]
 return copy.deepcopy(dict(version=1,seed_sha256=digest(seed),state_sha256=digest(state),metadata={k:v for k,v in state.items() if k not in ('records','ledger')},new_records=[r for r in state['records'] if r['connection_id'] not in before],record_order=[r['connection_id'] for r in state['records']],ledger_updates=updates,ledger_removed=removed))
def unpack(seed,delta):
 if delta['version']!=1 or digest(seed)!=delta['seed_sha256']:raise ValueError('wrong seed binding')
 records={r['connection_id']:r for r in seed['records']}
 for r in delta['new_records']:
  if r['connection_id'] in records:raise ValueError('duplicate delta identity')
  records[r['connection_id']]=r
 order=delta['record_order']
 if len(order)!=len(set(order)) or set(order)!=set(records):raise ValueError('wrong record scope')
 ledger=dict(seed['ledger'])
 for n in delta['ledger_removed']:del ledger[n]
 ledger.update(delta['ledger_updates']);state=copy.deepcopy(dict(delta['metadata'],records=[records[cid] for cid in order],ledger=ledger))
 if digest(state)!=delta['state_sha256']:raise ValueError('state digest mismatch')
 return state
