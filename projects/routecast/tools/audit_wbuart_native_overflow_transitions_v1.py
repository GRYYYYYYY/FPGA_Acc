"""Exact NET-owner overflow deltas and measured-residual native delta bounds."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_native_overflow_transitions_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replay(path,caps,payload):
 state={};counts=Counter();external={};pending=None;iteration=0;summary=Counter();per={}
 def tree(words):
  n,ignored,present,remaining,size=map(int,words[1:6]);nodes=set(map(int,words[6:]));assert len(nodes)==size;assert not ignored or not nodes;return n,nodes,present,remaining
 def observe(n,occ,cap):
  assert cap==caps[n];x=occ-counts[n];assert x>=0
  if n in external:assert external[n]==x
  external[n]=x
 def install(n,nodes):
  old=state.get(n,set())
  for k in old-nodes:counts[k]-=1;assert counts[k]>=0
  for k in nodes-old:counts[k]+=1
  state[n]=nodes
 with Path(path).open() as f,payload.open('x') as out:
  assert next(f)=='TRACE 1\n'
  for line in f:
   w=line.split();kind=w[0]
   if kind=='CP':
    tag,iteration=w[1],int(w[2]);incoming={};observed=[]
    for line in f:
     z=line.split()
     if z==['CE']:break
     if z[0]=='T':n,nodes,pr,rem=tree(z);incoming[n]=nodes
     else:observed.append(tuple(map(int,z[1:])))
    if tag not in ['initial','final_after_best_restore']:assert incoming==state
    else:
     state=incoming;counts=Counter(k for nodes in state.values() for k in nodes)
    external={}
    for n,occ,cap in observed:observe(n,occ,cap)
   elif kind=='Q':
    if w[4] in ['overuse','forced_connection']:observe(*map(int,w[5:8]))
   elif kind=='B':
    event,it,n,preserve,hold,decision=map(int,w[1:]);nn,old,pr,rem=tree(next(f).split());assert nn==n and old==state[n];pending=(event,it,n,old,pr,rem)
    for line in f:
     z=line.split()
     if z==['BE']:break
     observe(*map(int,z[1:]))
   elif kind=='E':
    event,it,n=map(int,w[1:]);assert pending[:3]==(event,it,n);nn,new,present,remaining=tree(next(f).split());assert nn==n and next(f).strip()=='EE';old=pending[3];delta=0;low=0;high=0;unknown=0
    for node in old^new:
     change=1 if node in new else -1;c=counts[node];cap=caps[node];delta+=max(0,c+change-cap)-max(0,c-cap)
     if node in external:
      x=external[node];d=max(0,c+x+change-cap)-max(0,c+x-cap);low+=d;high+=d
     elif change==1:
      if c>=cap:low+=1;high+=1
      else:high+=1;unknown+=1
     else:
      if c>cap:low-=1;high-=1
      else:low-=1;unknown+=1
    assert low<=high;install(n,new);pending=None;key='positive' if delta>0 else 'negative' if delta<0 else 'zero';summary['events']+=1;summary['NET_only_delta_'+key]+=1;summary['native_delta_provably_positive']+=low>0;summary['native_delta_provably_negative']+=high<0;summary['native_delta_exact']+=low==high;summary['events_with_unknown_external_on_changed_nodes']+=unknown>0;summary['incomplete_after']+=not present or remaining>0;per.setdefault(it,Counter()).update(events=1,NET_only_positive=int(delta>0),native_provably_positive=int(low>0));out.write(json.dumps({'event':event,'iteration':it,'net_id':n,'NET_owner_overflow_delta':delta,'native_overflow_delta_lower_bound':low,'native_overflow_delta_upper_bound':high,'unknown_external_changed_nodes':unknown,'complete_after':bool(present and remaining==0)})+'\n')
 assert pending is None
 return dict(summary),{str(k):dict(v) for k,v in per.items()}
def main():
 D.mkdir(exist_ok=False);W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';bindings={str(p):sha(p) for p in [Path(__file__),W]};rows=[];graphs={}
 for c in read(W)['comparisons']:
  s=read(c['specification']);ep=read(s['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:graphs[graph]=[int(e.get('capacity')) for _,e in ET.iterparse(graph) if e.tag=='node' and e.get('capacity') is not None];bindings[graph]=sha(graph)
  for ref in ['cold','source_restart']:
   out=E/'wbuart_native_evaluation_v1_2026-10-20/utility'/c['case']/'disabled' if ref=='cold' else E/'wbuart_target_source_restart_reference_v1_2026-10-20'/c['case'];p=out/'verification.json';proof=read(p);assert proof['independent_trace_replay_pass'] and all(sha(n)==h for n,h in proof['bindings'].items());d=D/c['case']/ref;d.mkdir(parents=True);payload=d/'events.jsonl';summary,per=replay(out/'owner_trace.tsv',graphs[graph],payload);rows.append({'case':c['case'],'reference':ref,'summary':summary,'per_iteration':per,'payload':str(payload)});bindings[str(p)]=sha(p);bindings[str(payload)]=sha(payload);print(c['case'],ref,summary,flush=True)
 assert len(rows)==18
 (D/'verification.json').write_text(json.dumps({'status':'ALL18_NATIVE_NET_TRANSITIONS_REPLAYED_WITH_EXTERNAL_RESIDUAL_BOUNDS','rows':rows,'bindings':bindings,'scope':'Exact NET-owner fullgraph deltas compare to forecast NET-ledger guard; actual native occupancy includes external reservations. For unmeasured external counts use conservative nonnegative-residual delta bounds, assuming unchanged external counts within NET routing as existing trace audit/source semantics. Positive NET-only deltas are not automatically positive actual native deltas. No necessity/causal or guard-relaxation/quality claim.'},indent=2)+'\n')
if __name__=='__main__':main()
