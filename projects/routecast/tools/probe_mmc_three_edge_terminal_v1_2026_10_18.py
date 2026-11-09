"""Frozen two/three-edge tail candidate diagnostic, never a model commit."""
import json,sys
from pathlib import Path
from bisect import bisect_right
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache
from terminal_assignment_feasibility_v1 import match

def main():
 old=R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'
 proof=R/'experiments/mmc_terminal_assignment_verification_v1_2026-10-18/verification.json'
 verification=json.loads(proof.read_text());assert verification['status']=='pass'
 bindings={**verification['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
 protocol=json.loads((old/'protocol.json').read_text())
 out=R/'experiments/mmc_three_edge_terminal_probe_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=protocol['inputs'],depths=[2,3],selection='All49 original initial-overused-IPIN classes, unchanged and source-only.',candidates='Exact depth2/depth3 directed tails from corresponding original prefix vertex; only same terminal pool. Positive capacities, no cycle, original budget and single-parent compatibility with every unchanged sibling query required. Keep minimum delay then edge IDs for each query/pin.',scope='Per-class matching diagnostic only. Cross-class sameNET compatibility, joint channel occupancy, objective and atomic admission pending. No model mutation or native benefit claim.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint'])
  offsets=f['row_offsets'];dest=f['dest_ranks'];ids=f['edge_ids'];caps=f['capacities']
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());original=json.loads((old/(case+'.json')).read_text())
   assert frame['graph_sha256']==digest and frame['scale']==rc.scale
   classes=original['classes'];selected={cid for c in classes for cid in c['connection_ids']}
   records={r['connection_id']:r for r in frame['records']};nets={records[cid]['net_id'] for cid in selected}
   siblings=defaultdict(list)
   for r in frame['records']:
    if r['net_id'] in nets:siblings[r['net_id']].append(r)
   needed={e for rs in siblings.values() for r in rs for e in r['answer']['physical_edge_ids']}
   slots={e:s for s,e in enumerate(ids) if e in needed};assert slots.keys()==needed
   parents={}
   for net,rs in siblings.items():
    counts=Counter()
    for r in rs:
     for e in r['answer']['physical_edge_ids']:counts[(dest[slots[e]],e)]+=1
    # Authenticated initial tree must have one incoming physical edge per node.
    incoming={}
    for (v,e),count in counts.items():
     assert v not in incoming or incoming[v]==e
     incoming[v]=e
    parents[net]=counts
   results=[];stats=Counter()
   for c in classes:
    sink=c['sink_RR'];capacity={int(p):n for p,n in c['available_IPIN_capacity'].items()}
    arms={}
    for depth in [2,3]:
     choices={};rejections=Counter()
     for cid in c['connection_ids']:
      r=records[cid];path=r['answer']['physical_edge_ids'];opts={}
      if len(path)<depth:
       choices[cid]=opts;rejections['short_path']+=1;continue
      prefix=path[:-depth];oldtail=path[-depth:];oldslots=[slots[e] for e in oldtail]
      anchor=bisect_right(offsets,oldslots[0])-1
      seen={r['source']}|{dest[slots[e]] for e in prefix}
      assert anchor in seen
      own_counts=Counter((dest[slots[e]],e) for e in path)
      fixed={v:e for (v,e),n in parents[r['net_id']].items() if n>own_counts[(v,e)]}
      prefix_delay=r['answer']['delay']-sum(rc.increment(s) for s in oldslots)
      def walk(u,left,tail,visited,delay):
       for s in range(offsets[u],offsets[u+1]):
        v=dest[s];e=ids[s]
        if caps[v]<=0 or v in visited:rejections['disabled_or_cycle']+=1;continue
        if v in fixed and fixed[v]!=e:rejections['sibling_parent_conflict']+=1;continue
        if left==2 and v not in capacity:continue
        if left==1 and v!=sink:continue
        if left>1 and v==sink:continue
        newdelay=delay+rc.increment(s)
        if newdelay>r['budget_integer']:rejections['budget']+=1;continue
        edges=tail+[e]
        if left==1:
         # The predecessor at the final arc is the actual selected IPIN.
         pin=u
         if not capacity.get(pin,0):continue
         candidate=(newdelay,edges)
         if pin not in opts or candidate<opts[pin]:opts[pin]=candidate
        else:walk(v,left-1,edges,visited|{v},newdelay)
      walk(anchor,depth,[],seen,prefix_delay)
      for pin,(delay,tail) in opts.items():assert rc.path(r['source'],sink,prefix+tail)==delay
      choices[cid]=opts
     matching=match({cid:opts.keys() for cid,opts in choices.items()},capacity)
     arms[str(depth)]=dict(matching=matching,candidate_pairs=sum(map(len,choices.values())),rejections=dict(rejections),candidates={cid:{pin:dict(delay=delay,tail_edges=tail) for pin,(delay,tail) in opts.items()} for cid,opts in choices.items()})
     stats['depth'+str(depth)+'_feasible_classes']+=int(matching['feasible'])
     stats['depth'+str(depth)+'_deficit']+=matching['hall_deficit']
    results.append(dict(sink_RR=sink,connection_ids=c['connection_ids'],arms=arms))
   summary=dict(case=case,classes=len(results),**stats)
   with (out/(case+'.json')).open('x') as stream:json.dump(dict(summary=summary,classes=results),stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.glob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='proposals_generated_independent_verification_pending',bindings=bindings,summaries=summaries,scope='No frame mutation, joint channel capacity, cross-class compatibility or objective admission.'),stream,indent=2)

if __name__=='__main__':main()
