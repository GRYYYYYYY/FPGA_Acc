"""All captured source/target matrices: bound identities, prior subset and samples."""
import json,hashlib,struct,array,sys
from pathlib import Path
from bound_allnet_map_query_v2 import Query
from bound_native_map_query_v1 import Query as Old
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_allnet_map_batch_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=read(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());rows=[];bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__)):sha(__file__),str(R/'tools/bound_allnet_map_query_v2.py'):sha(R/'tools/bound_allnet_map_query_v2.py')}
 for group in ['source','target']:
  for c in read(D/(group+'_manifest.json'))['cases']:
   if not c['allmap_enabled']:continue
   case=c['target_case'];p=Path(c['output'])/'allmap.bin';timing=E/'wbuart_frame_timings_v1_2026-10-20'/case/'initial_connection_criticalities.json'
   with p.open('rb') as f:
    while True:
     line=f.readline()
     if not line:raise ValueError('missing DATA')
     if line==b'DATA\n':break
    data=f.read()
   digest=hashlib.sha256(data).hexdigest();words=array.array('I');words.frombytes(data)
   if sys.byteorder!='little':words.byteswap()
   assert max(words)<=0x7f7fffff;del words,data
   q=Query(p,c['endpoint'],timing,digest);old=Old(Path(c['reference_output'])/'map_query.tsv',c['endpoint'],timing);pairs=0
   for (pin,node),values in old.values.items():
    got=struct.unpack_from('<ff',q.data,q.offset+(q.targets[old.targets[pin]]*q.n+node)*8);assert got==values;pairs+=1
   mapping={x['local_sink_pin']:x['connection_id'] for x in read(timing) if x['native_net_id']==0};samples=0;kw=dict(graph_sha256=q.graph_sha256,endpoint_sha256=q.endpoint_sha256)
   for line in (Path(c['output'])/'expected_cost.tsv').read_text().splitlines()[1:]:
    w=line.split();value=q.query(int(w[4]),mapping[int(w[3])],w[6],upstream_bits=w[8],**kw);assert struct.pack('>f',value).hex()==w[9];samples+=1
   rows.append({'case':case,'matrix_pairs':q.n*len(q.targets),'connections':len(q.connections),'extra_native_pins':q.extra_native_pins,'prior_subset_pairs_bit_equal':pairs,'actual_samples_bit_equal':samples,'payload_sha256':digest});q.close();print(case,'ALLNET_MATRIX_PASS',flush=True)
   for x in [p,timing,Path(c['endpoint'])]:bindings[str(x)]=sha(x)
 assert len(rows)==12
 (D/'independent_matrix_verification_v1.json').write_text(json.dumps({'status':'ALL12_ALLNET_NATIVE_MATRICES_PRIOR_SUBSETS_ACTUAL_SAMPLES_AND_DOMAINS_PASS','rows':rows,'bindings':bindings,'scope':'Native oracle endpoint-table qualification only, actual samples remain NET0; no allNET search, full model quality or paid benefit.'},indent=2)+'\n');print('ALL12_MATRIX_PASS',sum(x['actual_samples_bit_equal'] for x in rows),flush=True)
if __name__=='__main__':main()
