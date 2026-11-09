"""Current CID identity and complete explicit heap-work replay for preferred policy."""
from pathlib import Path
import json,array,sys,re,hashlib
from native_connection_work_trace_replay_v1 import replay
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 N=R/'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19';tp=N/'terminal.json';assert json.loads(tp.read_text())['status']=='ALL3_NATIVE_FULL_PHYSICAL_CANONICAL_AND_EXPIRY_PASS_WORK_REPLAY_PENDING';O=R/'experiments/mmc_preferred_NET_connection_replay_v1_2026-10-19';O.mkdir(exist_ok=False);rows=[];bindings={}
 for case in ['episode_01','episode_02','episode_03']:
  d=N/case;proof=d/'verification.json';p=json.loads(proof.read_text());assert p['all_native_physical_and_canonical_pass']
  for name,h in p['bindings'].items():assert sha(name)==h
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());qs={q['connection_id']:q for q in meta['connections']};assert set(qs)==set(range(115572));targets={(meta['net_names'][str(q['net_id'])],q['source'],q['sink']):cid for cid,q in qs.items()};assert len(targets)==115572
  trace=d/'connection_trace.tsv';v=replay(trace);assert v['router_success'];mapping={};inverse={}
  for (net,pin),info in v['pins'].items():
   if not pin:continue
   key=(v['nets'][net]['name'],v['pins'][net,0]['rr'],info['rr'])
   if key not in targets:continue
   cid=targets[key];assert cid not in mapping;mapping[cid]=(net,pin);inverse[net,pin]=cid
  assert set(mapping)==set(qs);counters={'heap_pushes':v['heap_pushes_by_native_pin'],'heap_pops':v['heap_pops_by_native_pin'],'successful_operations':v['successful_operations'],'failed_attempts':v['failed_attempts']};folder=O/case;folder.mkdir();totals={};vectors={}
  for name,counter in counters.items():
   assert set(counter)<=set(inverse);values=array.array('Q',[counter[mapping[cid]] for cid in range(115572)]);assert values.itemsize==8
   if name=='successful_operations':assert min(values)>=1
   f=folder/(name+'.u64');f.write_bytes(values.tobytes());vectors[name]={'path':str(f),'sha256':sha(f),'byteorder':sys.byteorder,'values':115572};totals[name]=sum(values)
  native=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',(d/'native.log').read_text());assert len(native)==1;netops,conns,push,pop=map(int,native[0]);assert totals['successful_operations']==conns==v['successful'];assert totals['heap_pushes']==push==v['attributed_heap_pushes'];assert totals['heap_pops']==pop==v['attributed_heap_pops'];assert totals['failed_attempts']==v['failed'];assert all(not v['pins'][mapping[cid]]['initially_reached'] for cid in qs)
  rows.append({'case':case,'NET_operations':netops,'connection_operations':conns,'heap_pushes':push,'heap_pops':pop,'failed_attempts':v['failed'],'outside_sink_work':0,'CID_count':115572,'vectors':vectors,'iterations':v['iterations']})
  for f in [proof,ep,trace]:bindings[str(f)]=sha(f)
  print('PREFERRED_CONNECTION_REPLAY_PASS',case,flush=True)
 for f in [tp,Path(__file__).resolve(),R/'tools/native_connection_work_trace_replay_v1.py']:bindings[str(f)]=sha(f)
 (O/'verification.json').write_text(json.dumps({'status':'ALL3_CURRENT_CID_EXPLICIT_HEAP_WORK_REPLAY_PASS','rows':rows,'bindings':bindings,'scope':'All current CID identities and heap work; independent raw arithmetic verifier and primary utility gate still pending.'},indent=2)+'\n')
if __name__=='__main__':main()
