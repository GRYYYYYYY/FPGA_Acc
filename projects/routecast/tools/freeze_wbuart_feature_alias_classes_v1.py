"""Exact raw-feature classes, frozen without opening target labels."""
import json,hashlib,sys
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_feature_alias_classes_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 if sys.byteorder!='little':raise ValueError('source f64 matrices are little endian')
 D.mkdir(exist_ok=False);source=E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json';proof=E/'wbuart_graph_signal_learning_v1_2026-10-20/independent_verification_v1.json';contract=E/'feature_alias_bounds_contract_v1_2026-10-20/verification.json'
 for p in [source,proof,contract]:assert all(sha(name)==h for name,h in read(p)['bindings'].items())
 bindings={str(p):sha(p) for p in [source,proof,contract,Path(__file__)]};(D/'protocol.json').write_text(json.dumps({'policy':'All9 cases,26 main and11 static/prior ablation raw columns. Exact little-endian f64 row-byte equality, no quantization, target counts, RR IDs as feature, threshold or model selection. Group IDs follow first member in sorted original resource-ID order. SHA is descriptive; full row bytes are the grouping key.','scope':'Alias limits cover only pointwise functions of this fixed vector; global graph models or additional context are not bounded. Later target-label bounds/oracles remain retrospective diagnostics, not predictors.','bindings':bindings},indent=2)+'\n');rows=[]
 for r in read(source)['rows']:
  blob=Path(r['matrix']).read_bytes();ids=read(r['resource_ids']);assert len(blob)==len(ids)*26*8
  for mode,d in [('main',26),('ablation',11)]:
   groups={}
   for i,node in enumerate(ids):
    key=blob[i*26*8:(i*26+d)*8];groups.setdefault(key,[]).append(node)
   out=D/r['case']/mode;out.mkdir(parents=True);p=out/'classes.json';p.write_text(json.dumps([{'class':i,'RRs':nodes,'signature_sha256':hashlib.sha256(key).hexdigest()} for i,(key,nodes) in enumerate(groups.items())],separators=(',',':'))+'\n');rows.append({'case':r['case'],'mode':mode,'columns':d,'raw_matrix':r['matrix'],'resource_ids':r['resource_ids'],'classes':str(p),'resources':len(ids),'class_count':len(groups),'largest_class':max(map(len,groups.values()))});bindings[str(p)]=sha(p)
 assert len(rows)==18
 (D/'classes_frozen.json').write_text(json.dumps({'status':'ALL18_EXACT_INPUT_ONLY_ALIAS_CLASS_PARTITIONS_FROZEN','rows':rows,'target_labels_read':False,'bindings':bindings},indent=2)+'\n');print('ALL18_ALIAS_CLASSES_FROZEN')
if __name__=='__main__':main()
