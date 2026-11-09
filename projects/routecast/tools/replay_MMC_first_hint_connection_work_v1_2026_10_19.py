"""Explicit sink snapshots -> current-layout CID vectors; no historical identity transfer."""
import pathlib,json,hashlib,array,sys
from collections import defaultdict
from native_connection_work_trace_replay_v1 import replay
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 N=R/'experiments/mmc_first_hint_connection_work_v2_2026-10-19';tp=N/'terminal.json'
 if not tp.exists():raise SystemExit('NOT_READY: all6 measurement equivalence required; no output created')
 t=json.loads(tp.read_text());assert t['status']=='ALL6_OBSERVER_RUNS_MATCH_CURRENT_REFERENCE_BYTES_WORK_AND_EXPIRY' and len(t['rows'])==6;O=R/'experiments/mmc_first_hint_connection_work_replay_v1_2026-10-19';O.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [tp,N/'execution_protocol.json',pathlib.Path(__file__).resolve(),R/'tools/native_connection_work_trace_replay_v1.py']};rows=[]
 for row in t['rows']:
  case,arm=row['case'],row['arm'];D=N/case/arm;proof=D/'equivalence.json';p=json.loads(proof.read_text());assert p['row']==row and row['status']=='EXACT_CURRENT_REFERENCE_BYTES_WORK_AND_EXPIRY_PASS'
  for f,h in p['bindings'].items():assert sha(pathlib.Path(f))==h
  ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';meta=json.loads(ep.read_text());qs={q['connection_id']:q for q in meta['connections']};assert set(qs)==set(range(115572));targets={(meta['net_names'][str(q['net_id'])],q['source'],q['sink']):cid for cid,q in qs.items()};assert len(targets)==115572;trace=D/'connection_trace.tsv';v=replay(trace);assert v['router_success'];native_map={};inverse={}
  for (net,pin),pininfo in v['pins'].items():
   if not pin:continue
   key=(v['nets'][net]['name'],v['pins'][net,0]['rr'],pininfo['rr'])
   if key not in targets:continue
   cid=targets[key];assert cid not in native_map and (net,pin) not in inverse;native_map[cid]=(net,pin);inverse[net,pin]=cid
  assert set(native_map)==set(qs);active=set(v['successful_operations'])|set(v['failed_attempts'])|{k for k,x in v['heap_pushes_by_native_pin'].items() if x}|{k for k,x in v['heap_pops_by_native_pin'].items() if x};assert active<=set(inverse)
  counters={'heap_pushes':v['heap_pushes_by_native_pin'],'heap_pops':v['heap_pops_by_native_pin'],'successful_operations':v['successful_operations'],'failed_attempts':v['failed_attempts']};folder=O/(case+'__'+arm);folder.mkdir();vectors={};data={}
  for name,counter in counters.items():
   values=array.array('Q',[counter[native_map[cid]] for cid in range(115572)]);assert values.itemsize==8;f=folder/(name+'.u64');f.write_bytes(values.tobytes());vectors[name]=dict(path=str(f),sha256=sha(f),typecode='Q',itemsize=8,values=115572,byteorder=sys.byteorder);data[name]=values
  assert min(data['successful_operations'])>=1 and sum(data['successful_operations'])==v['successful']==row['successful_sink_operations'];assert sum(data['failed_attempts'])==v['failed']==row['failed_sink_attempts'];assert sum(data['heap_pushes'])==v['attributed_heap_pushes']==row['attributed_heap_pushes'] and sum(data['heap_pops'])==v['attributed_heap_pops']==row['attributed_heap_pops'];native_push=sum(x['native_heap_pushes'] for x in v['iterations']);native_pop=sum(x['native_heap_pops'] for x in v['iterations']);assert native_push-sum(data['heap_pushes'])==row['outside_sink_heap_pushes'] and native_pop-sum(data['heap_pops'])==row['outside_sink_heap_pops']
  mf=folder/'CID_native_pin_mapping.json';write(mf,[dict(connection_id=cid,native_net=native_map[cid][0],native_pin=native_map[cid][1]) for cid in range(115572)]);summary=dict(case=case,arm=arm,CIDs=115572,all_current_identity_keys_unique=True,native_heap_pushes=native_push,native_heap_pops=native_pop,attributed_heap_pushes=sum(data['heap_pushes']),attributed_heap_pops=sum(data['heap_pops']),outside_sink_heap_pushes=row['outside_sink_heap_pushes'],outside_sink_heap_pops=row['outside_sink_heap_pops'],successful_operations=v['successful'],failed_attempts=v['failed'],distinct_repeated_CIDs=sum(n>1 for n in data['successful_operations']),repeat_successful_operations=sum(n-1 for n in data['successful_operations']),initially_reached_manifest_CIDs=sum(v['pins'][native_map[cid]]['initially_reached'] for cid in qs),iterations=v['iterations'],vectors=vectors,mapping=str(mf));assert summary['initially_reached_manifest_CIDs']==0;rows.append(summary)
  for f in [proof,trace,ep,mf,pathlib.Path(p['reference_proof'])]:bindings[str(f)]=sha(f)
  for desc in vectors.values():bindings[desc['path']]=desc['sha256']
  print('CURRENT_CID_WORK_REPLAY_PASS',case,arm,'heap',native_push,'distinct_repeat_CIDs',summary['distinct_repeated_CIDs'],flush=True)
 write(O/'verification.json',dict(status='ALL6_CURRENT_EXPLICIT_CONNECTION_SNAPSHOTS_AND_CURRENT_CID_BINDINGS_PASS',rows=rows,bindings=bindings,scope='Current episode identities joined by exact native NET name and RR source/sink; no reused historical query mapping. All115572CID zeros/vectors retained, measured heap deltas and successful/failed operations only. Independent raw arithmetic/identity audit pending. No causal perNET work attribution, policy benefit, elapsed-time or unseen-family claim.'))
if __name__=='__main__':main()
