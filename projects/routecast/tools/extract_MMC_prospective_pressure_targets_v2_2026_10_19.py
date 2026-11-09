"""Read admitted traces only; emit disjoint prefix and future payloads."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from array import array
from prospective_pressure_temporal_split_v1 import split
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 root=R/'experiments/mmc_prospective_pressure_trace_replay_v2_2026-10-19';proof=root/'verification.json'
 if not proof.exists():raise SystemExit('NOT_READY: independently admitted traces required')
 v=json.loads(proof.read_text());assert v['status']=='all3_native_traces_independently_replayed'
 for p,h in v['bindings'].items():assert sha(p)==h,p
 protocol=R/'experiments/mmc_prospective_pressure_protocol_v2_2026-10-19/protocol.json';spec=json.loads(protocol.read_text());cmd=spec['native_commands'][0]['argv'];graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(graph)==spec['bindings'][str(graph)]
 caps=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 out=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19';out.mkdir();rows=[];bindings={str(proof):sha(proof),str(protocol):sha(protocol),str(graph):sha(graph),str(pathlib.Path(__file__).resolve()):sha(__file__),str(R/'tools/prospective_pressure_temporal_split_v1.py'):sha(R/'tools/prospective_pressure_temporal_split_v1.py')}
 for name in spec['episodes']:
  p=root/(name+'.json');admitted=json.loads(p.read_text());trace=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/name/'cold/owner_trace.tsv';assert sha(trace)==admitted['bindings'][str(trace)]
  with trace.open('rb') as f:data=split(f,caps)
  assert data['iteration_stats']==admitted['iteration_stats'];d=out/name;d.mkdir()
  feature=dict(schema='MMC_FIRST_CHECKPOINT_OVERFLOW_FEATURES_V1',case=name,policy='cold',graph_sha256=sha(graph),cutoff_iteration=1,phase='iteration_end_after_local_opins',RR_domain_size=len(caps),overflow_units_by_rr=data['first_overflow'])
  target=dict(schema='MMC_STRICT_FUTURE_CHECKPOINT_TARGETS_V1',case=name,policy='cold',first_target_iteration=2,last_target_iteration=data['checkpoints'][-1]['iteration'],targets=data['targets'])
  write(d/'features.json',feature);write(d/'targets.json',target);write(d/'work_features.json',dict(observed_iteration=1,work=data['first_work']));write(d/'work_targets.json',dict(first_target_iteration=2,last_target_iteration=target['last_target_iteration'],totals=data['future_work']))
  bindings[str(p)]=sha(p);bindings[str(trace)]=sha(trace)
  for q in d.iterdir():bindings[str(q)]=sha(q)
  rows.append(dict(episode=name,first_checkpoint_end_byte=data['first_checkpoint_end_byte'],future_iterations=len(data['checkpoints'])-1,features_sha256=sha(d/'features.json'),targets_sha256=sha(d/'targets.json')))
 write(out/'verification.json',dict(status='all3_admitted_traces_split_at_iteration1',bindings=bindings,episodes=rows,forecast_metrics_pending=True,scope='Strictly separate first iteration from future pressure and work. No time or unseen-family claim.'))
if __name__=='__main__':main()
