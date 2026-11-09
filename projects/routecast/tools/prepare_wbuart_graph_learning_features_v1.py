"""Join audited source-only raw messages/static RR/prior native state."""
import json,math,time
from array import array
from pathlib import Path
from collections import Counter
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_graph_learning_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def main():
 D.mkdir(exist_ok=False);F=E/'wbuart_endpoint_graph_signals_v1_2026-10-20';H=E/'wbuart_preroute_heterograph_v1_2026-10-20';design=E/'wbuart_graph_signal_learning_design_v1_2026-10-20/protocol.json';inventory=E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json';proof=F/'independent_verification_v1.json'
 assert all(sha(p)==h for p,h in read(proof)['bindings'].items());assert all(sha(p)==h for p,h in read(design)['bindings'].items());raw=read(F/'verification.json');controls=read(inventory)['rows'];graphs={};rows=[];bindings={str(p):sha(p) for p in [Path(__file__),design,inventory,proof,F/'verification.json']};cols=read(design)['static_columns']+raw['rows'][0]['columns']
 for r in raw['rows']:
  begin=time.perf_counter();reference=next(x for x in controls if x['case']==r['case'] and (x['initializer'],x['timing_policy'],x['priority'])==('native_retained','warm_timing_round_updated','MAP'));digest=r['graph_sha256']
  if digest not in graphs:
   gd=H/'graphs'/digest;nodes={n['id']:n for n in lines(gd/'RR_nodes.jsonl')};incoming=Counter();outgoing=Counter()
   for e in lines(gd/'physical_edges.jsonl'):incoming[e['sink']]+=1;outgoing[e['source']]+=1
   graphs[digest]=(nodes,incoming,outgoing)
  nodes,incoming,outgoing=graphs[digest];prior={int(n):v for n,v in read(reference['source_frame'])['ledger'].items()};messages={q['RR']:q['values'] for q in lines(r['feature_file'])};resources=lines(reference['resources']);ids=sorted(n['id'] for n in resources);assert all(nodes[n]['type'] in ['CHANX','CHANY'] and nodes[n]['capacity']==1 for n in ids);features=array('d')
  for n in ids:
   rr=nodes[n];loc=rr['loc'];values=[math.log1p(rr['capacity']),loc['xlow'],loc['xhigh'],loc['ylow'],loc['yhigh'],int(rr['type']=='CHANX'),int(rr['direction']=='INC_DIR'),int(rr['direction']=='DEC_DIR'),math.log1p(incoming[n]),math.log1p(outgoing[n]),math.log1p(prior.get(n,0))]+[math.log1p(x) for x in messages[n]];assert len(values)==26;features.extend(values)
  out=D/r['case'];out.mkdir(parents=True);p=out/'raw_features.f64';p.write_bytes(features.tobytes());ip=out/'resource_ids.json';ip.write_text(json.dumps(ids)+'\n');rows.append({'case':r['case'],'matrix':str(p),'resource_ids':str(ip),'rows':len(ids),'columns':26,'source_frame':reference['source_frame'],'resources':reference['resources'],'feature_seconds':time.perf_counter()-begin})
  for path in [p,ip,Path(reference['source_frame']),Path(reference['resources']),Path(r['feature_file'])]:bindings[str(path)]=sha(path)
  print('GRAPH_LEARNING_FEATURES',r['case'],len(ids),flush=True)
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_SOURCE_ONLY_RAW_FEATURE_MATRICES_FROZEN','rows':rows,'columns':cols,'static_columns':11,'target_labels_read':False,'fit_transforms':False,'bindings':bindings,'scope':'Known strictly prior native route is an explicit input; its acquisition remains paid/shared. No raw RR IDs as feature, no candidate or target route input. WBUART exposed development.'},indent=2)+'\n')
if __name__=='__main__':main()
