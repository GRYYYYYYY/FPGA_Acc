"""Independent replay of the archived-layout cold observer equivalence trace."""
import pathlib,json,re,hashlib,xml.etree.ElementTree as ET
from array import array
from native_owner_trace_replay_v1 import replay
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 D=R/'experiments/mmc_cold_observer_equivalence_v1_2026-10-19';proof=D/'receipt.json'
 if not proof.exists():raise SystemExit('NOT_READY: cold equivalence receipt required')
 v=json.loads(proof.read_text());assert v['status']=='ARCHIVED_COLD_BYTES_AND_INTEGER_WORK_EQUAL'
 for p,h in v['bindings'].items():assert sha(p)==h,p
 epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=pathlib.Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];caps=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 out=D/'cold';trace=out/'owner_trace.tsv';result,state=replay(trace,caps,v['native_work']['rows']);log=(out/'native.log').read_text();totals=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',log);assert len(totals)==1
 assert tuple(sum(x[k] for x in result['iteration_stats']) for k in ['NET_operations','connection_operations','heap_pushes','heap_pops'])==tuple(map(int,totals[0]))
 names={ep['net_names'][str(q['net_id'])]:q['net_id'] for q in ep['connections']};unions={};current=None
 for line in (out/'output.route').open():
  w=line.split()
  if w and w[0]=='Net':
   current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
   if current is not None:assert current in names and current not in unions;unions[current]=set()
  elif w and w[0]=='Node:':assert current in names;unions[current].add(int(w[1]))
 assert set(unions)==set(names) and len(unions)==55300
 for name,nodes in unions.items():
  value=state[names[name]];assert value[:3]==(0,1,0) and set(value[3])==nodes
 known=set(names.values());assert all(net in known or value[0] for net,value in state.items() if value[1])
 bindings={**v['bindings'],**{str(p):sha(p) for p in [proof,epfile,graph,pathlib.Path(__file__).resolve(),R/'tools/native_owner_trace_replay_v1.py']}}
 result.update(status='ARCHIVED_COLD_OBSERVER_EQUIVALENCE_AND_TRACE_REPLAY_PASS',bindings=bindings,all55300_final_NET_unions_match=True,all_checkpoint_and_work_records_replayed=True,scope='Archived exposed layout only; observer cold compatibility verified, not new-target prediction quality or timing gain.')
 with (D/'independent_trace_verification_v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'],len(result['iteration_stats']),flush=True)
if __name__=='__main__':main()
