"""Independent set-owner projection of certified trace NET transitions; no routing."""
import json,sys,time,os,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def project(path,caps):
 state={};ledger=Counter();hist=Counter();by_iteration=defaultdict(Counter);seq=0;pending=None;duplicates=set();max_extra=0;witnesses=[]
 def tree(w):
  nonlocal max_extra
  assert w[0]=='T' and len(w)>=6;net,ignored,present,remaining,count=map(int,w[1:6]);raw=tuple(map(int,w[6:]));assert len(raw)==count and raw==tuple(sorted(raw));extra=count-len(set(raw));max_extra=max(max_extra,extra)
  if extra:duplicates.add(net)
  return net,(ignored,present,remaining,raw)
 def nodes(value):return set(value[3]) if value[0]==0 else set()
 def assign(net,value):
  old=nodes(state[net]) if net in state else set();new=nodes(value)
  for n in old-new:
   ledger[n]-=1;assert ledger[n]>=0
   if ledger[n]==0:del ledger[n]
  for n in new-old:ledger[n]+=1
  state[net]=value
 with path.open() as f:
  assert f.readline()=='TRACE 1\n'
  def line():
   s=f.readline();assert s,'truncated';return s.split()
  while True:
   w=line();tag=w[0]
   if tag=='CP':
    incoming={};phase=w[1]
    while True:
     z=line()
     if z==['CE']:break
     if z[0]=='T':n,v=tree(z);assert n not in incoming;incoming[n]=v
     else:assert z[0]=='V'
    if phase=='initial':
     assert not state
     for n,v in incoming.items():assign(n,v)
    elif phase=='final_after_best_restore':
     assert incoming.keys()==state.keys()
     for n,v in incoming.items():assign(n,v)
    else:assert incoming==state
   elif tag=='B':
    event,it,net=map(int,w[1:4]);assert pending is None and event==seq+1;n,v=tree(line());assert n==net and v==state[net]
    while True:
     z=line()
     if z==['BE']:break
     assert z[0]=='V'
    pending=(event,it,net);seq=event
   elif tag=='E':
    assert pending==tuple(map(int,w[1:]));n,v=tree(line());assert n==pending[2] and line()==['EE'];old=nodes(state[n]);new=nodes(v);delta=0;facts=[]
    for node in old^new:
     d=1 if node in new else -1;before=ledger.get(node,0);after=before+d;assert after>=0;change=max(0,after-caps[node])-max(0,before-caps[node]);delta+=change
     if pending[1]>1 and len(witnesses)<8:facts.append(dict(node=node,owners_before=before,owner_delta=d,capacity=caps[node],overflow_delta=change))
    kind='positive' if delta>0 else 'negative' if delta<0 else 'zero';hist[kind]+=1;by_iteration[pending[1]][kind]+=1
    if delta>0 and pending[1]>1 and len(witnesses)<8:witnesses.append(dict(event=pending[0],iteration=pending[1],NET=n,unique_NET_overflow_delta=delta,facts=facts))
    assign(n,v);pending=None
   elif tag in ['Q','S']:pass
   elif tag=='END':assert pending is None and int(w[3])==seq and not f.read();break
   else:raise AssertionError(tag)
 assert sum(hist.values())==seq
 return dict(transitions=seq,unique_NET_transition_signs=dict(hist),by_iteration={str(k):dict(v) for k,v in by_iteration.items()},positive_unique_NET_transitions_after_iteration1=sum(v['positive'] for k,v in by_iteration.items() if k>1),NETs_with_duplicate_RR_occurrences=len(duplicates),maximum_repeated_RR_occurrences_per_tree=max_extra,first8_post_first_iteration_positive_witnesses=witnesses)

def main():
 E=R/'experiments';old=E/'mmc_native_owner_trace_replay_v2_2026-10-18';root=E/'mmc_native_unique_NET_overflow_projection_v1_2026-10-18';root.mkdir();cp=old/'cohort_verification.json';c=json.loads(cp.read_text());assert c['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass'];ep=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';d=json.loads(ep.read_text());graph=Path(d['inputs']['graph']['path']);assert sha(graph)==d['graph_sha256'];caps=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(caps)==904438;bindings={**closure([Path(__file__)]),str(graph):sha(graph),str(cp):sha(cp)};protocol=dict(bindings=bindings,scope='Exact unique nonignored NET-owner overflow on observed native trees, excluding native non-NET external occupancy. This is the estimator-style owner-count projection, not an assertion about full native occupancy or identical model candidate/budget/timing state.',no_rerouting=True,no_guard_relaxation=True);(root/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');s=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(root/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=s[19]))+'\n');rows=[]
 for case in ['case_01','case_02','case_03']:
  for arm in ['off','on']:
   p=old/case/(arm+'.json');v=json.loads(p.read_text());assert c['bindings'][str(p)]==sha(p) and v['status']=='pass';trace=E/f'mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{arm}/owner_trace.tsv';assert v['bindings'][str(trace)]==sha(trace);row=project(trace,caps);assert row['transitions']==v['setup_attempts'];row.update(case=case,arm=arm);folder=root/case;folder.mkdir(exist_ok=True);out=folder/(arm+'.json');out.open('x').write(json.dumps(dict(bindings={str(p):sha(p),str(trace):sha(trace)},**row),indent=2)+'\n');bindings[str(out)]=sha(out);rows.append({k:v for k,v in row.items() if k!='first8_post_first_iteration_positive_witnesses'});(root/'stages.json').write_text(json.dumps(rows,indent=2)+'\n');print('UNIQUE_NET_OVERFLOW_PROJECTED',case,arm,row['unique_NET_transition_signs'],row['positive_unique_NET_transitions_after_iteration1'],flush=True)
 (root/'results.json').write_text(json.dumps(dict(status='all6_exact_unique_NET_occupancy_overflow_projections_complete',bindings=bindings,cases=rows,scope=protocol['scope']),indent=2)+'\n')
if __name__=='__main__':main()
