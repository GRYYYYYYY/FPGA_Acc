import json,hashlib,struct,math
from pathlib import Path
from bound_allnet_map_query_v1 import Query
from bound_native_map_query_v1 import Query as Old
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_allnet_map_preflight_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 manifest=json.loads((D/'manifest.json').read_text());case=manifest['cases'][1];path=D/'on/allmap.bin'
 with path.open('rb') as f:
  while f.readline()!=b'DATA\n':pass
  offset=f.tell();payload=hashlib.sha256(f.read()).hexdigest()
 timing=E/'wbuart_frame_timings_v1_2026-10-20/w096/episode_01/initial_connection_criticalities.json';q=Query(path,case['endpoint'],timing,payload);old=Old(E/'wbuart_map_probe_targets_v1_2026-10-20/w096/episode_01/map_query.tsv',case['endpoint'],timing);t=json.loads(timing.read_text());pins={x['local_sink_pin']:x['connection_id'] for x in t if x['native_net_id']==0};checked=0
 for (pin,node),values in old.values.items():
  target=old.targets[pin];new=struct.unpack_from('<ff',q.data,q.offset+(q.targets[target]*q.n+node)*8);assert new==values;checked+=1
 kw=dict(graph_sha256=q.graph_sha256,endpoint_sha256=q.endpoint_sha256);samples=0
 for line in (D/'on/expected_cost.tsv').read_text().splitlines()[1:]:
  w=line.split();value=q.query(int(w[4]),pins[int(w[3])],w[6],upstream_bits=w[8],**kw);assert struct.pack('>f',value).hex()==w[9];samples+=1
 nonfinite={};negative={}
 for target,index in q.targets.items():
  for n in range(q.n):
   values=struct.unpack_from('<ff',q.data,q.offset+(index*q.n+n)*8)
   if any(not math.isfinite(x) for x in values):nonfinite[q.kinds[n]]=nonfinite.get(q.kinds[n],0)+1
   if any(x<0 for x in values):negative[q.kinds[n]]=negative.get(q.kinds[n],0)+1
 rejected=0
 for fn in [lambda:q.query(0,999999,'00000000',**kw),lambda:q.query(0,0,'00000000',**dict(kw,endpoint_sha256='0'*64)),lambda:q.query(q.connections[0][0],0,'7fc00000',**kw),lambda:Query(path,case['endpoint'],timing,'0'*64)]:
  try:fn()
  except ValueError:rejected+=1
  else:raise AssertionError('invalid admitted')
 out={'status':'PREFLIGHT_ALLNET_ADAPTER_SUBSET_SAMPLES_AND_BASIC_REJECTIONS_PASS','payload_sha256':payload,'native_targets':len(q.targets),'connections':len(q.connections),'extra_native_pins':q.extra_native_pins,'NET0_subset_pairs':checked,'actual_samples':samples,'nonfinite_pairs_by_kind':nonfinite,'negative_pairs_by_kind':negative,'basic_rejections':rejected,'scope':'One case only; comprehensive independent parser/corruption and all9 source-target qualification pending.','bindings':{str(p):sha(p) for p in [Path(__file__),R/'tools/bound_allnet_map_query_v1.py',path,D/'verification.json',timing]}};q.close();(D/'adapter_verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
if __name__=='__main__':main()
