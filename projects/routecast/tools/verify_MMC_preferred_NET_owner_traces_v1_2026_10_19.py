"""Independent new-layout trace replay; no baseline-byte equivalence assumed."""
import json,pathlib,hashlib,re,struct,xml.etree.ElementTree as ET
from array import array
from native_owner_trace_replay_v1 import replay
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 N=R/'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19';I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';O=R/'experiments/mmc_preferred_NET_owner_replay_v1_2026-10-19'
 terminal=N/'terminal.json'
 if not terminal.exists():raise SystemExit('NOT_READY: native cohort not terminal; no replay directory created')
 assert json.loads(terminal.read_text())['status']=='ALL3_NATIVE_FULL_PHYSICAL_CANONICAL_AND_EXPIRY_PASS_WORK_REPLAY_PENDING'
 specpath=R/'experiments/mmc_preferred_NET_native_utility_protocol_v1_2026-10-19/protocol.json';spec=json.loads(specpath.read_text());bindings={str(specpath):sha(specpath),str(terminal):sha(terminal),str(pathlib.Path(__file__).resolve()):sha(__file__),str(R/'tools/native_owner_trace_replay_v1.py'):sha(R/'tools/native_owner_trace_replay_v1.py')}
 graph=pathlib.Path(spec['jobs'][0]['argv'][spec['jobs'][0]['argv'].index('--read_rr_graph')+1]);meta=json.loads((I/spec['jobs'][0]['case']/'demand/endpoints.json').read_text());assert meta['graph_sha256']==sha(graph);bindings[str(graph)]=sha(graph)
 caps=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(caps)==904438;O.mkdir();rows=[]
 for job in spec['jobs']:
  name=job['case'];arm='preferred'
  p=N/name/'verification.json';v=json.loads(p.read_text());assert v['all_native_physical_and_canonical_pass'] and len(v['rows'])==1;row=v['rows'][0];assert row['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert row['policy_arm']==arm and row['preload_state']['all_bits_match_fixed_one_pseudo_iteration'] and row['preload_state']['all_nodes_checked']==904438
  for q,h in v['bindings'].items():assert sha(q)==h,q
  d=N/name
  risk=pathlib.Path(job['environment_set']['ROUTECAST_EXCESS_PRELOAD']);hint={int(line.split()[0]) for line in risk.read_text().splitlines()[1:]}
  arrays=[]
  for filename in ['preload_state.bin','expiry_before.bin','expiry_after.bin']:
   header,data=(d/filename).read_bytes().split(b'\n',1);assert header==b'RCACCBITS1 904438' and len(data)==4*904438;arrays.append([x[0] for x in struct.iter_unpack('<I',data)])
  initial,before,after=arrays;changed={n for n,(a,b) in enumerate(zip(before,after)) if a!=b};assert changed<=hint
  assert all(before[n]==initial[n] and after[n]==0x3f800000 for n in hint)
  assert row['expiry_state']['all_nonhint_words_preserved'] and row['expiry_state']['all_nodes_checked']==904438 and row['expiry_state']['changed_cost_words']==len(changed)
  trace=d/'owner_trace.tsv';result,state=replay(trace,caps,row['native_work']['rows']);log=(d/'native.log').read_text();totals=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',log);assert len(totals)==1
  assert tuple(sum(x[k] for x in result['iteration_stats']) for k in ['NET_operations','connection_operations','heap_pushes','heap_pops'])==tuple(map(int,totals[0]))
  epfile=I/name/'demand/endpoints.json';ep=json.loads(epfile.read_text());names={ep['net_names'][str(q['net_id'])]:q['net_id'] for q in ep['connections']};unions={};current=None
  with (d/'output.route').open() as f:
   for line in f:
    w=line.split()
    if w and w[0]=='Net':
     current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
     if current is not None:assert current in names and current not in unions;unions[current]=set()
    elif w and w[0]=='Node:':assert current in names;unions[current].add(int(w[1]))
  assert set(unions)==set(names) and len(unions)==55300
  for net,nodes in unions.items():
   value=state[names[net]];assert value[:3]==(0,1,0) and set(value[3])==nodes
  known=set(names.values());assert all(net in known or value[0] for net,value in state.items() if value[1])
  local={str(q):sha(q) for q in [p,trace,epfile,d/'native.log',d/'output.route']};result.update(status='pass',episode=name,policy_arm=arm,bindings=local,final_physical_NET_unions_equal=True,exact_native_work_counters_equal=True,external_occupancy_assumed_zero=False)
  q=O/(name+'_'+arm+'.json');write(q,result);bindings.update(local);bindings[str(q)]=sha(q);rows.append(dict(episode=name,policy_arm=arm,proof=str(q),status='pass'));print('REPLAY PASS',name,arm,flush=True)
 write(O/'verification.json',dict(status='all3_preferred_NET_native_traces_independently_replayed',bindings=bindings,runs=rows,native_utility_gate_pending=True,complete_workflow_gain_pending=True,strict_unseen_family_admitted=False))
if __name__=='__main__':main()
