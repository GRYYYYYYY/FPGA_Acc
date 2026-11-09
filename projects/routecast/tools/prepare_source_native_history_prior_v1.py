"""Independent IEEE754 decoding to exact model excess, source epoch bound."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'source_final_history_parity_v1_2026-10-20';D=E/'source_native_history_prior_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def decode(bits):
 sign=bits>>31;exponent=(bits>>23)&255;mantissa=bits&((1<<23)-1);assert sign==0 and 0<exponent<255
 return Fraction((1<<23)|mantissa)*Fraction(2)**(exponent-127-23)
def main():
 proof=I/'verification.json';v=json.loads(proof.read_text());assert v['status']=='SOURCE_FINAL_HISTORY_EXACT_ROUTE_PARITY_AND_ALL_NODE_F32_EXPORT_PASS';assert all(sha(p)==h for p,h in v['bindings'].items());D.mkdir(exist_ok=False);path=I/'work/source_final_rr_history.tsv';history={};values={}
 with path.open() as f:
  header=f.readline().split('\t');assert int(header[2])==v['iterations']
  for line in f:
   tag,node,cap,occ,bits,hexvalue=line.strip().split('\t');node=int(node);value=decode(int(bits,16));assert node==len(values) and value>=1 and value.denominator==1;values[node]=value.numerator
   if value>1:history[str(node)]=value.numerator-1
 assert len(values)==v['nodes'] and len(history)==v['nonunit_history_nodes'] and max(values.values())==v['maximum_history'];manifest=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19/source_manifest.json';case=json.loads(manifest.read_text())['cases'][0];assert case['case']=='w160/source';cmd=case['command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1]);source=Path(case['output'])/'output.route';prior=dict(schema='SOURCE_FINAL_NATIVE_HISTORY_EXCESS_V1',graph_sha256=sha(graph),source_route_sha256=sha(source),source_case='w160/source',nodes=len(values),source_iterations=v['iterations'],history=history,conversion='Exact unsigned f32 IEEE754 rational decoding; require integral acc_cost>=1, history=acc_cost-1. 1+history equals original native acc_cost exactly.',lifecycle='Frozen source-end negotiated history after best-tree restore; available before target forecast. Model round updates, if studied, must be additive and separately declared.',scope='Prospective source prior only, no target-native state, no forecast quality or native utility admission.')
 p=D/'prior.json';p.write_text(json.dumps(prior)+'\n');assert all(Fraction(1+history.get(str(n),0))==v for n,v in values.items());bindings={str(p):sha(p),str(path):sha(path),str(proof):sha(proof),str(graph):sha(graph),str(source):sha(source),str(Path(__file__)):sha(__file__)};(D/'verification.json').write_text(json.dumps(dict(status='ALL129090_SOURCE_F32_VALUES_EXACT_INTEGER_EXCESS_PRIOR_PASS',nodes=len(values),nonzero_excess_nodes=len(history),maximum_excess=max(history.values()),bindings=bindings,scope=prior['scope']),indent=2)+'\n');print('ALL129090_SOURCE_F32_VALUES_EXACT_INTEGER_EXCESS_PRIOR_PASS',len(history),max(history.values()))
if __name__=='__main__':main()
