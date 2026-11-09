import json,tempfile,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from native_owner_trace_replay_v1 import replay
def fixture(multiplicity=False,external=False,retry=False):
 caps=[1,1,2 if multiplicity or external else 1,1]
 initial={0:(0,1,1,(0,)),1:(0,1,0,(2,2) if multiplicity else (2,)),2:(1,0,0,())}
 lines=['TRACE 1'];state=dict(initial);event=decision=0;blocks=[]
 def t(net,value):
  ig,has,remaining,nodes=value
  return ' '.join(map(str,['T',net,ig,has,remaining,len(nodes),*nodes]))
 def cp(tag):
  lines.append('CP '+tag+' '+('0' if tag=='initial' else '1'))
  lines.extend(t(n,v) for n,v in state.items());lines.append('CE')
 def attempt(net,reason,new,occ=None):
  nonlocal event,decision
  event+=1;decision+=1;start=len(lines);node=2 if reason=='overuse' else -1
  lines.append(f'Q {decision} 1 {net} {reason} {node} {occ if occ is not None else -1} {caps[2] if node==2 else -1}')
  lines.append(f'B {event} 1 {net} {int(net==0)} 0 {decision}');lines.append(t(net,state[net]))
  if occ is not None:lines.append(f'V 2 {occ} {caps[2]}')
  lines.append('BE');lines.append(f'E {event} 1 {net}');lines.append(t(net,new));lines.append('EE')
  state[net]=new;blocks.append((start,len(lines)))
 cp('initial');cp('iteration_begin')
 if retry:attempt(0,'remaining_sinks',(0,1,1,(0,1)))
 attempt(0,'remaining_sinks',(0,1,0,(0,1,2)))
 attempt(1,'overuse',(0,1,0,(3,)),3 if multiplicity or external else 2)
 cp('routed_before_local_opins');lines.append('S 1 2 2 10 5');cp('iteration_end_after_local_opins');cp('final_after_best_restore');lines.append(f'END 1 {decision} {event}')
 return lines,caps,blocks
work=[dict(iteration=1,rerouted_NET_operations=2,rerouted_connection_operations=2,heap_pushes=10,overused_RR_nodes=0)]
D=R/'experiments/native_owner_trace_replay_core_v1_2026-10-18';D.mkdir();positive=[];negative=[]
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'trace.tsv'
 for name,opts in [('owner_transfer',{}),('multiplicity',{'multiplicity':True}),('external_residual',{'external':True}),('retry',{'retry':True})]:
  lines,caps,blocks=fixture(**opts);path.write_text('\n'.join(lines)+'\n');result,state=replay(path,caps,work)
  assert result['decisions']==(3 if opts.get('retry') else 2)
  assert result['incomplete_attempts']==int(bool(opts.get('retry')))
  assert result['co_owner_guard_witness_edges']==[dict(owner=0,selected_NET=1,observations=1)]
  if opts.get('external'):assert result['measured_external_residual_observations']['positive']==2
  positive.append(name)
 lines,caps,blocks=fixture();text='\n'.join(lines)+'\n';q2=next(x for x in lines if x.startswith('Q 2 '));b1=next(x for x in lines if x.startswith('B 1 '))
 corrupt={}
 corrupt['missing_E']=text.replace('E 1 1 0\nT 0 0 1 0 3 0 1 2\nEE\n','')
 corrupt['duplicate_Q']=text.replace(q2,q2+'\n'+q2)
 corrupt['stale_B']=text.replace(b1+'\nT 0 0 1 1 1 0',b1+'\nT 0 0 1 1 1 1')
 corrupt['wrong_checkpoint']=text.replace('CP routed_before_local_opins 1\nT 0 0 1 0 3 0 1 2','CP routed_before_local_opins 1\nT 0 0 1 0 3 0 1 3')
 corrupt['bad_exact_stat']=text.replace('S 1 2 2 10 5','S 1 2 2 11 5')
 corrupt['bad_capacity']=text.replace(q2,q2.rsplit(' ',1)[0]+' 2')
 corrupt['external_changed_mid_NET']=text.replace('V 2 2 1','V 2 3 1')
 corrupt['truncated_END']=text.rsplit('END',1)[0]
 corrupt['wrong_iteration']=text.replace('CP iteration_end_after_local_opins 1','CP iteration_end_after_local_opins 2')
 corrupt['unsorted_RRs']=text.replace('T 0 0 1 0 3 0 1 2','T 0 0 1 0 3 0 2 1',1)
 corrupt['missing_checkpoint_NET']=text.replace('CP routed_before_local_opins 1\nT 0 0 1 0 3 0 1 2\nT 1 0 1 0 1 3\nT 2 1 0 0 0','CP routed_before_local_opins 1\nT 0 0 1 0 3 0 1 2\nT 1 0 1 0 1 3')
 for name,value in corrupt.items():
  assert value!=text,name
  path.write_text(value)
  try:replay(path,caps,work)
  except AssertionError:negative.append(name)
  else:raise AssertionError(('corrupt trace accepted',name))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings={str(p):sha(p) for p in [Path(__file__).resolve(),R/'tools/native_owner_trace_replay_v1.py']},positive_fixtures=positive,rejected_corruptions=negative,scope='Synthetic streaming ownership/count/order fixtures, including multiplicity, retry and non-NET residual. Not native graph legality, STA, real-trace admission or causal evidence.'),f,indent=2)
print('OWNER TRACE CORE PASS',len(positive),len(negative),flush=True)
