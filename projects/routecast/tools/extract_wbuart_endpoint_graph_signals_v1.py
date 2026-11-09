"""Freeze all9 label-free multigraph endpoint message tables."""
import json
from pathlib import Path
from endpoint_graph_signals_v1 import extract,COLUMNS
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_endpoint_graph_signals_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def main():
 D.mkdir(exist_ok=False);H=E/'wbuart_preroute_heterograph_v1_2026-10-20';source=H/'verification.json';proof=H/'independent_verification_v1.json';contract=E/'endpoint_graph_signals_contract_v1_2026-10-20/verification.json'
 for p in [proof,contract]:assert all(sha(name)==h for name,h in read(p)['bindings'].items())
 v=read(source);assert all(sha(name)==h for name,h in v['bindings'].items());files=[source,proof,contract,Path(__file__),R/'tools/endpoint_graph_signals_v1.py'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'policy':'All9 input cases; exact source NET/CID/span and sink CID/span messages at0,1,2 directed physical edges, reverse for sink messages. Parallel edges/selfloops counted as distinct walks. Raw integer features; no label normalization, learned coefficient or candidate path input.','columns':COLUMNS,'bindings':bindings,'scope':'Development features only. No trained model/quality/family admission. Depth2 fixed before evaluation; no depth/feature tuning from target scores.'},indent=2)+'\n');graphs={};outputs=[];tables={}
 for r in v['rows']:
  digest=r['graph_sha256']
  if digest not in graphs:
   graphdir=H/'graphs'/digest;nodes=lines(graphdir/'RR_nodes.jsonl');edges=[(e['source'],e['sink']) for e in lines(graphdir/'physical_edges.jsonl')];graphs[digest]=([n['id'] for n in nodes],edges)
  ids,edges=graphs[digest];case=Path(r['directory']);queries=lines(case/'NET_RR_incidence.jsonl');nets={n['net_id']:n for n in lines(case/'NET_features.jsonl')};features=extract(ids,edges,queries,nets);out=D/r['case'];out.mkdir(parents=True);p=out/'features.jsonl'
  with p.open('x') as f:
   for n in sorted(features):f.write(json.dumps({'RR':n,'values':features[n]},separators=(',',':'))+'\n')
  outputs.append({**r,'feature_file':str(p),'columns':COLUMNS,'RR_rows':len(features)});bindings[str(p)]=sha(p);tables[r['case']]=features;print('ENDPOINT_FEATURES',r['case'],len(features),flush=True)
 sensitivity=[]
 for width in ['w096','w128','w160']:
  for a,b in [('episode_01','episode_02'),('episode_01','episode_03'),('episode_02','episode_03')]:
   x,y=tables[width+'/'+a],tables[width+'/'+b];assert set(x)==set(y);sensitivity.append({'width':width,'a':a,'b':b,'RR_rows_changed':sum(x[n]!=y[n] for n in x)})
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_RAW_SOURCE_ONLY_ENDPOINT_MESSAGE_TABLES_PRODUCED','rows':outputs,'layout_sensitivity':sensitivity,'bindings':bindings,'target_payloads_read':False,'independent_audit_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
