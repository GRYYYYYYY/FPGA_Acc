"""Build a fresh single-owner ledger from authenticated endpoint context and route.

Does not establish native FULL/STA acceptance or publish state. The caller must
bind that evidence and selected bundle identity. No branch-budget guarantee is
imposed on retained native reference paths; new searches retain their own budget.
"""
from collections import defaultdict
from pathlib import Path
from audit_native_route import NET,NODE
from route_ledger_state import RouteLedgerState
from pre_route_endpoints import sha

def physical_paths(path):
 result=defaultdict(list);name=None;parents={};previous=None;switch=None
 for line in Path(path).read_text().splitlines():
  m=NET.match(line)
  if m:
   name=m[2]
   if name in result:raise ValueError('duplicate NET name')
   result[name]=[];parents={};previous=None;switch=None
  m=NODE.match(line)
  if not m:
   if line.lstrip().startswith('Node:'):raise ValueError('unparsed route node')
   continue
  if name is None:raise ValueError('node before NET')
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':
   if parents:raise ValueError('multiple SOURCE roots')
   parents[node]=((node,None),)
  elif kind=='SINK':
   if previous not in parents:raise ValueError('invalid terminal predecessor')
   result[name].append(parents[previous]+((node,switch),))
  elif node not in parents:
   if previous not in parents:raise ValueError('invalid branch predecessor')
   parents[node]=parents[previous]+((node,switch),)
  previous=node;switch=int(m[3])
 return dict(result)

def import_native_ledger(ctx,route_path):
 before=sha(route_path);paths=physical_paths(route_path);f=ctx.rc.fields
 grouped=defaultdict(list)
 for q in ctx.context[5]:
  grouped[(ctx.endpoint_metadata['net_names'][str(q['net_id'])],q['source'],q['sink'])].append(q)
 observed=defaultdict(list)
 excluded={x['net'] for x in ctx.endpoint_metadata['excluded_nets'] if x['reason']=='explicit exclude_root_clocks policy'}
 for name,rows in paths.items():
  if name in excluded and rows:raise ValueError('excluded clock has physical paths')
  for path in rows:observed[(name,path[0][0],path[-1][0])].append(path)
 if set(observed)!=set(grouped):raise ValueError('native endpoint cohort mismatch')
 state=RouteLedgerState(ctx)
 for key,queries in grouped.items():
  rows=observed[key]
  if len(rows)!=len(queries):raise ValueError('native terminal multiplicity mismatch')
  if len(rows)>1 and len(set(rows))>1:raise ValueError('ambiguous repeated class terminal paths')
  for q,path in zip(sorted(queries,key=lambda q:q['connection_id']),sorted(rows)):
   net=q['net_id'];node=q['source'];used={node};incoming={};edges=[];delay=ctx.rc.initial(node)
   if ctx.context[2][node].get('type')!='SOURCE':raise ValueError('invalid SOURCE type')
   for dst,switch in path[1:]:
    if dst in used:raise ValueError('cyclic physical path')
    candidates=[s for s in range(f['row_offsets'][node],f['row_offsets'][node+1]) if f['dest_ranks'][s]==dst and f['switch_ids'][s]==switch]
    if len(candidates)!=1:raise ValueError('missing or ambiguous physical arc')
    slot=candidates[0];eid=f['edge_ids'][slot];edges.append(eid);delay+=ctx.rc.increments[slot];incoming[dst]=(node,eid);node=dst;used.add(node)
   if node!=q['sink'] or ctx.context[2][node].get('type')!='SINK':raise ValueError('invalid SINK type')
   if any(n in state.parents[net] and state.parents[net][n]!=v for n,v in incoming.items()):raise ValueError('native tree has multiple parents')
   state.parents[net].update(incoming);state.ledger.update(used-state.unions[net]);state.unions[net].update(used)
   state.records[q['connection_id']]={**q,'mode':'NATIVE_REFERENCE_RETAINED','answer':{'status':'FOUND','physical_edge_ids':edges,'delay':delay}}
 if any(c>f['capacities'][n] for n,c in state.ledger.items()):raise ValueError('native capacity overflow')
 if sha(route_path)!=before:raise ValueError('native route changed during import')
 return state
