"""Full-frame independent path, ownership and integer-scaled objective replay.

Does not import model validators or scoring functions. Graph/RC decoding and
authenticated input loading remain shared trusted components.
"""
import json,sys,math
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from versioned_digest_cache_v1 import Cache

def main():
 source=R/'experiments/mmc_objective_terminal_subset_v1_2026-10-18'
 receipt=json.loads((source/'receipt.json').read_text())
 bindings={**receipt['bindings'],str(source/'receipt.json'):sha(source/'receipt.json'),**closure([Path(__file__)])}
 protocol=json.loads((source/'protocol.json').read_text());out=R/'experiments/mmc_objective_terminal_batch_verification_v1_2026-10-18';out.mkdir()
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint']);caps=f['capacities']
  span={}
  for i,n in enumerate(nodes):
   if n.get('type') in ('CHANX','CHANY'):
    loc=n.find('loc');span[i]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  weight=rc.scale//(20*10**9)
  for case,data in protocol['inputs'].items():
   base,crit,b=load(data['endpoint'],data['node_base_proof'],data['criticality_directory'],len(nodes),rc.scale);bindings.update(b)
   frame=json.loads(Path(data['frame']).read_text());assert frame['graph_sha256']==digest and frame['history']=={} and frame['scale']==rc.scale
   artifact=json.loads((source/(case+'.json')).read_text())
   finite=json.loads((R/'experiments/mmc_global_terminal_subset_v1_2026-10-18'/(case+'.json')).read_text())
   previous=json.loads((R/'experiments/mmc_resource_constrained_terminal_v1_2026-10-18'/(case+'.json')).read_text())
   classes=sorted((c for c in previous['classes'] if c['resource_assignment']['feasible']),key=lambda c:c['sink_RR'])
   replacements={i:{r['connection_id']:r for r in c['replacements']} for i,c in enumerate(classes)}
   records={r['connection_id']:r for r in frame['records']};assert len(records)==115572==frame['required_connections']==frame['completed_connections']
   chosen={r['connection_id']:r for r in artifact['chosen_replacements']};assert len(chosen)==len(artifact['chosen_replacements']) and chosen.keys()<=records.keys()
   groups=defaultdict(list)
   for r in records.values():groups[r['net_id']].append(r)
   D=math.lcm(*(c['criticality_denominator'] for c in crit.values()))
   units={cid:c['criticality_numerator']*(D//c['criticality_denominator']) for cid,c in crit.items()};assert all(0<=c<=D for c in units.values())
   needed={e for r in records.values() for e in r['answer']['physical_edge_ids']}
   needed.update(e for rows in replacements.values() for r in rows.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   def interpret(rs):
    source_rr=rs[0]['source'];net=rs[0]['net_id'];owned={source_rr};parents={};users={};raw=0
    assert caps[source_rr]>0
    for r in rs:
     old=records[r['connection_id']]
     assert {k:v for k,v in old.items() if k!='answer'}=={k:v for k,v in r.items() if k!='answer'}
     assert r['source']==source_rr and r['net_id']==net and r['answer']['status']=='FOUND'
     u=source_rr;seen={u};delay=rc.initial(u);c=units[r['connection_id']]
     for e in r['answer']['physical_edge_ids']:
      s=slots[e];assert f['row_offsets'][u]<=s<f['row_offsets'][u+1] and f['edge_ids'][s]==e
      v=f['dest_ranks'][s];assert v not in seen and caps[v]>0
      assert v not in parents or parents[v]==(u,e)
      parents[v]=(u,e);seen.add(v);owned.add(v);users[v]=max(users.get(v,0),c)
      delay+=rc.increment(s);u=v
     assert u==r['sink'] and delay==r['answer']['delay']<=r['budget_integer']
     raw+=c*delay
    return owned,users,raw
   oldledger=Counter();newledger=Counter();oldweights=Counter();newweights=Counter();oldraw=0;newraw=0;oldaudits={}
   pattern_nets={p['net_id'] for p in finite['NET_patterns']}
   for net,rs in groups.items():
    oa=interpret(rs);na=interpret([chosen.get(r['connection_id'],r) for r in rs])
    oldledger.update(oa[0]);newledger.update(na[0]);oldraw+=oa[2];newraw+=na[2]
    oldweights.update({p:D-c for p,c in oa[1].items()});newweights.update({p:D-c for p,c in na[1].items()})
    if net in pattern_nets:oldaudits[net]=oa
   assert dict(oldledger)=={int(p):n for p,n in frame['ledger'].items() if n}
   assert all(newledger[p]<=max(oldledger[p],caps[p]) for p in oldledger.keys()|newledger.keys())
   def full_numerator(ledger,weights,raw):
    return raw+sum(w*(base[p]*(1+max(0,ledger[p]-caps[p]))+weight*span.get(p,0)) for p,w in weights.items())
   before=full_numerator(oldledger,oldweights,oldraw);after=full_numerator(newledger,newweights,newraw)
   actual_global=Fraction(after-before,D)
   assert actual_global==Fraction(artifact['summary']['self_consistent_global_objective_delta'])<=0
   # Independently price every finite local NET pattern at original epoch.
   scores={};reported={(p['net_id'],p['mask']):Fraction(p['objective_delta']) for p in artifact['NET_pattern_objectives']}
   for p in finite['NET_patterns']:
    if not p['valid']:continue
    net=p['net_id'];mask=p['mask'];old=oldaudits[net]
    updates={cid:r for i,rows in replacements.items() if mask>>i&1 for cid,r in rows.items() if r['net_id']==net}
    new=interpret([updates.get(r['connection_id'],r) for r in groups[net]])
    def frozen(a):
     return a[2]+sum((D-c)*(base[n]*(1+max(0,oldledger[n]-int(n in old[0])-caps[n]+1))+weight*span.get(n,0)) for n,c in a[1].items())
    value=Fraction(frozen(new)-frozen(old),D);assert value==reported[(net,mask)];scores[(net,mask)]=value
   net_masks=defaultdict(int)
   for i,rows in replacements.items():
    for net in {r['net_id'] for r in rows.values()}:net_masks[net]|=1<<i
   best=None;bestmask=None;valid_count=0
   assert len(artifact['subsets'])==len(finite['subsets'])
   for row,oldrow in zip(artifact['subsets'],finite['subsets']):
    mask=oldrow['mask'];violations=sorted(net for net,nmask in net_masks.items() if scores.get((net,mask&nmask),Fraction(0))>0)
    valid=oldrow['valid'] and not violations
    assert row==dict(mask=mask,resource_valid=oldrow['valid'],objective_increased_NETs=violations,valid=valid)
    key=(-mask.bit_count(),oldrow['total_overflow'],oldrow['changed_queries'],tuple(classes[i]['sink_RR'] for i in range(len(classes)) if mask>>i&1))
    if valid:
     valid_count+=1
     if best is None or key<best:best=key;bestmask=mask
   assert bestmask==artifact['summary']['chosen_mask'] and valid_count==artifact['summary']['valid_subsets']
   expected={cid:r for i,rows in replacements.items() if bestmask>>i&1 for cid,r in rows.items()};assert expected==chosen
   overflow=sum(max(0,n-caps[p]) for p,n in newledger.items());assert overflow==artifact['summary']['proposal_overflow']
   summary=dict(case=case,connections_checked_each_state=len(records),NETs_checked_each_state=len(groups),objective_patterns_checked=len(scores),subsets_checked=len(finite['subsets']),selected_classes=-best[0],overflow=overflow,full_before_objective=str(Fraction(before,D)),full_after_objective=str(Fraction(after,D)),global_objective_delta=str(actual_global))
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(source/(case+'.json')):sha(source/(case+'.json')) for case in protocol['inputs']})
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,scope='Independent complete old/new frame path and integer-scaled full objective reconstruction, all local objective constraints and finite subset ranking. Shared graph/RC decoding and input loaders. No atomic commit, native or forecast benefit established.'),stream,indent=2)

if __name__=='__main__':main()
