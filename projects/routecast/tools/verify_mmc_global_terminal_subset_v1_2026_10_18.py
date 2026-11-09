"""Independent path interpreter, ownership tables and exhaustive subset audit."""
import json,sys,itertools
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache

def main():
 d=R/'experiments/mmc_global_terminal_subset_v1_2026-10-18';receipt=json.loads((d/'receipt.json').read_text())
 bindings={**receipt['bindings'],str(d/'receipt.json'):sha(d/'receipt.json'),**closure([Path(__file__)])}
 protocol=json.loads((d/'protocol.json').read_text());out=R/'experiments/mmc_global_terminal_subset_verification_v1_2026-10-18';out.mkdir()
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,_,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint']);caps=f['capacities']
  for case,data in protocol['inputs'].items():
   frame=json.loads(Path(data['frame']).read_text());assert frame['graph_sha256']==digest
   result=json.loads((d/(case+'.json')).read_text())
   proposals=json.loads((R/'experiments/mmc_resource_constrained_terminal_v1_2026-10-18'/(case+'.json')).read_text())
   original=json.loads((R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18'/(case+'.json')).read_text())
   pools={c['sink_RR']:set(map(int,c['available_IPIN_capacity'])) for c in original['classes']}
   classes=sorted((c for c in proposals['classes'] if c['resource_assignment']['feasible']),key=lambda c:c['sink_RR'])
   assert result['class_order']==[c['sink_RR'] for c in classes]
   records={r['connection_id']:r for r in frame['records']};ledger={int(p):n for p,n in frame['ledger'].items()}
   replacements={i:{r['connection_id']:r for r in c['replacements']} for i,c in enumerate(classes)}
   net_classes=defaultdict(set)
   for i,rows in replacements.items():
    for r in rows.values():net_classes[r['net_id']].add(i)
   groups=defaultdict(list)
   for r in records.values():
    if r['net_id'] in net_classes:groups[r['net_id']].append(r)
   needed={e for rs in groups.values() for r in rs for e in r['answer']['physical_edge_ids']}
   needed.update(e for rows in replacements.values() for r in rows.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   def interpret(rs):
    parent={};owned=set();source=rs[0]['source'];net=rs[0]['net_id']
    for r in rs:
     if r['source']!=source or r['net_id']!=net:raise ValueError('identity')
     old=records[r['connection_id']]
     if {k:v for k,v in old.items() if k!='answer'}!={k:v for k,v in r.items() if k!='answer'}:raise ValueError('metadata')
     u=source;seen={u};delay=rc.initial(u);owned.add(u)
     for e in r['answer']['physical_edge_ids']:
      s=slots[e]
      if not f['row_offsets'][u]<=s<f['row_offsets'][u+1]:raise ValueError('physical source')
      v=f['dest_ranks'][s]
      if v in seen or caps[v]<=0:raise ValueError('cycle/capacity')
      if v in parent and parent[v]!=(u,e):raise ValueError('parents')
      parent[v]=(u,e);seen.add(v);owned.add(v);delay+=rc.increment(s);u=v
     if u!=r['sink'] or delay!=r['answer']['delay'] or delay>r['budget_integer']:raise ValueError('RC/budget/target')
    return owned
   old_owned={n:interpret(rs) for n,rs in groups.items()};tables={};patterns={(r['net_id'],r['mask']):r for r in result['NET_patterns']}
   for net,indices in net_classes.items():
    ids=sorted(indices)
    for bits in itertools.product([False,True],repeat=len(ids)):
     mask=sum(1<<i for i,b in zip(ids,bits) if b)
     updates={cid:r for i,b in zip(ids,bits) if b for cid,r in replacements[i].items() if r['net_id']==net}
     try:owned=interpret([updates.get(r['connection_id'],r) for r in groups[net]])
     except ValueError:owned=None
     p=patterns[(net,mask)];assert p['valid']==(owned is not None)
     if owned is not None:assert p['added']==sorted(owned-old_owned[net]) and p['removed']==sorted(old_owned[net]-owned)
     tables[(net,mask)]=owned
   assert len(tables)==len(patterns)
   base=sum(max(0,n-caps[p]) for p,n in ledger.items());best=None;bestmask=None;valid_count=0
   assert len(result['subsets'])==1<<len(classes)
   for mask,row in enumerate(result['subsets']):
    assert row['mask']==mask
    selected=[i for i in range(len(classes)) if mask>>i&1];changes=Counter();invalid=[]
    for net,indices in net_classes.items():
     local=sum(1<<i for i in indices if mask>>i&1);owned=tables[(net,local)]
     if owned is None:invalid.append(net);continue
     for p in owned-old_owned[net]:changes[p]+=1
     for p in old_owned[net]-owned:changes[p]-=1
    growth=sorted(p for p,n in changes.items() if ledger.get(p,0)+n>max(ledger.get(p,0),caps[p]))
    unrepaired=sorted(p for i in selected for p in pools[classes[i]['sink_RR']] if ledger.get(p,0)+changes[p]>caps[p])
    total=base+sum(max(0,ledger.get(p,0)+n-caps[p])-max(0,ledger.get(p,0)-caps[p]) for p,n in changes.items())
    updates={cid:r for i in selected for cid,r in replacements[i].items()};changed=sum(r['answer']!=records[cid]['answer'] for cid,r in updates.items())
    valid=not invalid and not growth and not unrepaired
    assert row['valid']==valid and row['invalid_NETs']==sorted(invalid) and row['overflow_growth_nodes']==growth and row['unrepaired_selected_IPINs']==unrepaired
    assert row['total_overflow']==total and row['changed_queries']==changed and row['applied_classes']==len(selected)
    key=(-len(selected),total,changed,tuple(classes[i]['sink_RR'] for i in selected))
    if valid:
     valid_count+=1
     if best is None or key<best:best=key;bestmask=mask
   assert bestmask==result['summary']['chosen_mask'] and valid_count==result['summary']['valid_subsets']
   chosen={cid:r for i in range(len(classes)) if bestmask>>i&1 for cid,r in replacements[i].items()}
   assert chosen=={r['connection_id']:r for r in result['chosen_replacements']}
   summary=dict(case=case,NET_patterns_verified=len(tables),subsets_verified=len(result['subsets']),chosen_classes=-best[0],chosen_overflow=best[1],valid_subsets=valid_count)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,scope='Independent physical path interpreter, combined NET ownership, all finite apply/retain subsets and ranking. Shared graph/RC decoding; no alternate matching completeness, criticality objective admission, native or full-flow claim.'),stream,indent=2)

if __name__=='__main__':main()
