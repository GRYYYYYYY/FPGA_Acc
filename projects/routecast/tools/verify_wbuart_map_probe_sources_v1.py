"""Matrix coverage/identity, actual sample recombination and negative contracts."""
import json,hashlib,struct,math,tempfile
from pathlib import Path
from bound_native_map_query_v1 import Query
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_probe_on_qualification_v1_2026-10-20';OFF=E/'wbuart_map_probe_off_qualification_v1_2026-10-20';OLD=E/'wbuart_expected_cost_on_qualification_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bits(x):return struct.pack('>f',x).hex()
def reject(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('invalid query admitted')
def main():
 proof=D/'verification.json';assert read(proof)['status']=='ALL3_SOURCE_DISABLED_ZERO_PHYSICAL_CANONICAL_TRACE_AND_ORIGINAL_PATH_PARITY_PASS';manifest=read(D/'manifest.json');rows=[];total=0;negative=0;bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/bound_native_map_query_v1.py',proof,OFF/'verification.json',D/'manifest.json']}
 for c in manifest['cases']:
  out=Path(c['output']);off=OFF/'native'/f"w{c['width']:03d}"/c['utility_arm'];old=OLD/'native'/f"w{c['width']:03d}"/c['utility_arm'];a,b=read(out/'verification.json'),read(off/'verification.json');assert all(sha(p)==h for p,h in a['bindings'].items());assert all(a[k]==b[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_work']);assert sha(out/'owner_trace.tsv')==sha(off/'owner_trace.tsv') and sha(out/'output.route')==sha(off/'output.route') and sha(out/'expected_cost.tsv')==sha(old/'expected_cost.tsv');timing=E/'wbuart_frame_timings_v1_2026-10-20'/f"w{c['width']:03d}/source/initial_connection_criticalities.json";matrix=out/'map_query.tsv';adapter=Query(matrix,c['endpoint'],timing);kw={'graph_sha256':adapter.graph_sha256,'endpoint_sha256':adapter.endpoint_sha256};sample=0
  for line in (out/'expected_cost.tsv').read_text().splitlines()[1:]:
   w=line.split();pin,node=int(w[3]),int(w[4]);actual=adapter.query(node,pin,w[6],upstream_bits=w[8],**kw);assert bits(actual)==w[9],(c['case'],w,actual);sample+=1
  total+=sample;firstnode=next(iter(adapter.allowed));reject(lambda:adapter.query(firstnode,1,'00000000',**dict(kw,graph_sha256='0'*64)));reject(lambda:adapter.query(firstnode,1,'00000000',**dict(kw,endpoint_sha256='0'*64)));reject(lambda:adapter.query(firstnode,3,'00000000',**kw));reject(lambda:adapter.query(firstnode,1,'40000000',**kw));reject(lambda:adapter.query(firstnode,1,'00000000',upstream_bits='3f800000',**kw));unsupported=next(n for n in range(len(adapter.kinds)) if n not in adapter.allowed);reject(lambda:adapter.query(unsupported,1,'00000000',**kw));negative+=6
  if c['utility_arm']=='disabled':
   lines=matrix.read_text().splitlines();idx=next(i for i,l in enumerate(lines) if l.startswith('Q '))
   with tempfile.TemporaryDirectory(prefix='routecast_map_probe_') as td:
    p=Path(td)/'partial.tsv';p.write_text('\n'.join(lines[:idx]+lines[idx+1:])+'\n');reject(lambda:Query(p,c['endpoint'],timing));p=Path(td)/'duplicate.tsv';p.write_text('\n'.join(lines+[lines[idx]])+'\n');reject(lambda:Query(p,c['endpoint'],timing));p=Path(td)/'nonfinite.tsv';changed=list(lines);w=changed[idx].split();w[4]='7f800000';changed[idx]=' '.join(w);p.write_text('\n'.join(changed)+'\n');bad=Query(p,c['endpoint'],timing);reject(lambda:bad.query(int(w[2]),int(w[1]),'00000000',**kw));negative+=3
  nonfinite=sum(not all(math.isfinite(x) for x in pair) for pair in adapter.values.values());rows.append({'width':c['width'],'arm':c['utility_arm'],'domain_nodes':len(adapter.allowed),'native_endpoint_queries':2*len(adapter.values),'matrix_entries':len(adapter.values),'native_nonfinite_entries':nonfinite,'actual_samples_bit_exact_recombined':sample,'route_trace_work_and_original_samples_unchanged':True});print(rows[-1],flush=True)
  for p in [matrix,timing,Path(c['endpoint']),out/'verification.json',out/'expected_cost.tsv']:bindings[str(p)]=sha(p)
 assert len(rows)==6 and total==1634
 (D/'independent_probe_verification_v1.json').write_text(json.dumps({'status':'ALL6_SOURCE_MAP_QUERY_DOMAINS1634_EXPECTED_SAMPLES_AND_REJECTION_CONTRACTS_PASS','rows':rows,'samples':total,'invalid_rejections':negative,'bindings':bindings,'scope':'BoundedNET0 native API endpoint matrix and exact float32 recombination, not independent MAP algorithm or admissibility proof. Source fixtures only; no model heuristic/quality/gain claim. Nonfinite rows retained and queries reject them.'},indent=2)+'\n');print('BOUNDED_MAP_SOURCE_VERIFIED',total,negative)
if __name__=='__main__':main()
