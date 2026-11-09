"""Independent endpoint reconstruction and pernode directed-walk gather."""
import json
from pathlib import Path
from collections import defaultdict
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_endpoint_graph_signals_v1_2026-10-20';H=E/'wbuart_preroute_heterograph_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==9 and not v['target_payloads_read'];assert all(sha(name)==h for name,h in v['bindings'].items());graphs={};rows=[];checked=0
 for r in v['rows']:
  digest=r['graph_sha256']
  if digest not in graphs:
   directory=H/'graphs'/digest;nodes={n['id']:n for n in lines(directory/'RR_nodes.jsonl')};incoming=defaultdict(list);outgoing=defaultdict(list)
   for e in lines(directory/'physical_edges.jsonl'):incoming[e['sink']].append(e['source']);outgoing[e['source']].append(e['sink'])
   graphs[digest]=(nodes,incoming,outgoing)
  nodes,incoming,outgoing=graphs[digest];qs=lines(Path(r['directory'])/'NET_RR_incidence.jsonl');by_net=defaultdict(list);base={n:[0]*5 for n in nodes}
  for q in qs:by_net[q['net_id']].append(q)
  for net,items in by_net.items():
   source=items[0]['source'];xs=[];ys=[]
   for q in items:
    for key in ['source','sink']:
     loc=nodes[q[key]]['loc'];xs.extend([loc['xlow'],loc['xhigh']]);ys.extend([loc['ylow'],loc['yhigh']])
   span=max(xs)-min(xs)+max(ys)-min(ys)+2;base[source][0]+=1;base[source][1]+=len(items);base[source][2]+=span
   for q in items:base[q['sink']][3]+=1;base[q['sink']][4]+=span
  features=lines(r['feature_file']);assert len(features)==len(nodes)==r['RR_rows'] and {x['RR'] for x in features}==set(nodes)
  for item in features:
   n=item['RR'];expected=base[n]+[sum(base[a][i] for a in incoming[n]) for i in range(3)]+[sum(base[a][i] for mid in incoming[n] for a in incoming[mid]) for i in range(3)]+[sum(base[b][i] for b in outgoing[n]) for i in range(3,5)]+[sum(base[b][i] for mid in outgoing[n] for b in outgoing[mid]) for i in range(3,5)];assert item['values']==expected;checked+=len(expected)
  rows.append({'case':r['case'],'RR_rows':len(features)});print('ENDPOINT_SIGNAL_AUDIT',r['case'],flush=True)
 assert len(rows)==9
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL9_ENDPOINT_BASES_AND_TWO_EDGE_WALKS_INDEPENDENTLY_VERIFIED','rows':rows,'integer_feature_cells':checked,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Source-only raw feature correctness. No trained model, normalization, target score or family admission.'},indent=2)+'\n');print('ALL_ENDPOINT_SIGNALS_VERIFIED',checked)
if __name__=='__main__':main()
