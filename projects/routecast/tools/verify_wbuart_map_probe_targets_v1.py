"""All9 bound target matrices, original samples and same-graph frame rejection."""
import json,hashlib,struct,math,tempfile
from pathlib import Path
from bound_native_map_query_v1 import Query
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_probe_targets_v1_2026-10-20';OLD=E/'wbuart_expected_cost_targets_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bits(x):return struct.pack('>f',x).hex()
def reject(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('invalid query admitted')
def main():
 p=D/'verification.json';assert read(p)['status']=='ALL9_TARGET_EXPECTED_OBSERVER_PHYSICAL_CANONICAL_TRACE_AND_EXACT_PARITY_PASS';assert all(sha(n)==h for n,h in read(p)['bindings'].items());manifest=read(D/'manifest.json');rows=[];samples=0;negative=0;bindings={str(x):sha(x) for x in [Path(__file__),R/'tools/bound_native_map_query_v1.py',p,D/'manifest.json']}
 for c in manifest['cases']:
  case=c['target_case'];out=Path(c['output']);previous=OLD/case;assert sha(out/'expected_cost.tsv')==sha(previous/'expected_cost.tsv');timing=E/'wbuart_frame_timings_v1_2026-10-20'/case/'initial_connection_criticalities.json';matrix=out/'map_query.tsv';query=Query(matrix,c['endpoint'],timing);kw={'graph_sha256':query.graph_sha256,'endpoint_sha256':query.endpoint_sha256};num=0
  for line in (out/'expected_cost.tsv').read_text().splitlines()[1:]:
   w=line.split();assert bits(query.query(int(w[4]),int(w[3]),w[6],upstream_bits=w[8],**kw))==w[9];num+=1
  samples+=num;node=next(iter(query.allowed));reject(lambda:query.query(node,1,'00000000',**dict(kw,graph_sha256='0'*64)));reject(lambda:query.query(node,1,'00000000',**dict(kw,endpoint_sha256='0'*64)));reject(lambda:query.query(node,3,'00000000',**kw));unsupported=next(n for n in range(len(query.kinds)) if n not in query.allowed);reject(lambda:query.query(unsupported,1,'00000000',**kw));negative+=4
  other=next(x for x in manifest['cases'] if x['width']==c['width'] and x['target_case']!=case);other_timing=E/'wbuart_frame_timings_v1_2026-10-20'/other['target_case']/'initial_connection_criticalities.json';reject(lambda:Query(matrix,other['endpoint'],other_timing));negative+=1
  lines=matrix.read_text().splitlines();index=next(i for i,x in enumerate(lines) if x.startswith('Q '))
  with tempfile.TemporaryDirectory(prefix='routecast_target_map_') as td:
   partial=Path(td)/'partial.tsv';partial.write_text('\n'.join(lines[:index]+lines[index+1:])+'\n');reject(lambda:Query(partial,c['endpoint'],timing));duplicate=Path(td)/'duplicate.tsv';duplicate.write_text('\n'.join(lines+[lines[index]])+'\n');reject(lambda:Query(duplicate,c['endpoint'],timing));negative+=2
  rows.append({'case':case,'domain_nodes':len(query.allowed),'matrix_entries':len(query.values),'native_endpoint_queries':2*len(query.values),'nonfinite_entries':sum(not all(math.isfinite(x) for x in values) for values in query.values.values()),'actual_expected_samples_bit_exact':num,'same_graph_other_frame_rejected':True});print(rows[-1],flush=True)
  for path in [matrix,timing,Path(c['endpoint']),out/'expected_cost.tsv',out/'verification.json']:bindings[str(path)]=sha(path)
 assert len(rows)==9 and samples==3656
 (D/'independent_probe_verification_v1.json').write_text(json.dumps({'status':'ALL9_TARGET_BOUND_MAP_QUERY_MATRICES3656_ACTUAL_SAMPLES_AND_FRAME_REJECTIONS_PASS','rows':rows,'samples':samples,'invalid_rejections':negative,'bindings':bindings,'scope':'FixedNET0/CID0and1 bounded native API endpoints only. Native behavior/sample parity and exact interpolation demonstrated; no independent MAP implementation, general full-sketch heuristic, native-equivalent search or quality/gain claim.'},indent=2)+'\n');print('TARGET_MAP_PROBE_VERIFIED',samples,negative)
if __name__=='__main__':main()
