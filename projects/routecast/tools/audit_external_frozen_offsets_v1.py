"""Counterexample audit: one baseline edge-minus-RR offset versus actual native updates."""
import csv,json,hashlib,struct
from pathlib import Path
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_delay_perturbations_v1_2026-10-19';BASE=E/'prospective_external_family_clock_constraints_v1_2026-10-19';M=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';D=E/'prospective_external_family_frozen_offset_audit_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def f32(v):return struct.unpack('f',struct.pack('f',float(v)))[0]
def ibits(v):return struct.unpack('>I',struct.pack('>f',v))[0]
def rows(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def main():
 proof=read(P/'verification_v2.json');assert proof['passed'];assert all(sha(k)==h for k,h in proof['bindings'].items());D.mkdir(exist_ok=False);bindings={str(P/'verification_v2.json'):sha(P/'verification_v2.json'),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for entry in proof['rows']:
  case,mode=entry['case'],entry['mode'];old=BASE/case;new=P/case/mode;edges0={int(x['edge']):x for x in rows(old/'timing_edges.tsv')};edges1={int(x['edge']):x for x in rows(new/'timing_edges.tsv')};rr0={(int(x['net']),int(x['pin'])):f32(x['delay_s']) for x in rows(new/'initial_connections.tsv')};rr1={(int(x['net']),int(x['pin'])):f32(x['delay_s']) for x in rows(new/'updated_connections.tsv')};mapped=read(M/case/'external_edge_CID_bindings_v1.json');result=dict(case=case,mode=mode,external_edges=len(mapped));examples=[]
  for scope,col in [('max','value_max_or_setup_s'),('min','value_min_or_hold_s')]:
   bad=0;maxabs=0.;maxulp=0
   for q in mapped:
    e=q['edge'];key=q['native_net_id'],q['local_sink_pin'];offset=F(f32(edges0[e][col]))-F(rr0[key]);predict=f32(offset+F(rr1[key]));actual=f32(edges1[e][col]);ulp=abs(ibits(predict)-ibits(actual))
    if ulp:
     bad+=1;maxabs=max(maxabs,abs(predict-actual));maxulp=max(maxulp,ulp)
     if len(examples)<4:examples.append(dict(scope=scope,edge=e,native_net=key[0],pin=key[1],baseline_rr=rr0[key],updated_rr=rr1[key],frozen_offset=str(offset),predicted=predict,actual=actual,ULPs=ulp))
   result[scope]=dict(mismatches=bad,max_absolute_seconds=maxabs,max_ULPs=maxulp)
  result['examples']=examples;results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='examples'}),flush=True)
  for p in [old/'timing_edges.tsv',new/'timing_edges.tsv',new/'initial_connections.tsv',new/'updated_connections.tsv',M/case/'external_edge_CID_bindings_v1.json']:bindings[str(p)]=sha(p)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL9_FROZEN_SINGLE_OFFSET_NATIVE_EDGE_RECONSTRUCTION_AUDITED',rows=results,bindings=bindings,scope='Exact baseline edge-minus-net delay rational collapsed to one offset; candidate cast once to float32 and compared to actual native updated max/min edge values. No offset fitted to perturbations, no tolerance acceptance. Nominal packed mapping fixed; physical pin remapping remains untested.'),indent=2)+'\n')
if __name__=='__main__':main()
