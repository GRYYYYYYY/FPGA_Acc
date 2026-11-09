"""Crosscheck serialized RC oracle against printed native RR increments, bounded by rounding."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from tree_rc import TreeRC
out=Path('experiments/frisc_net49_sta_rc_crosscheck_2026-10-05')
if out.exists():raise ValueError('fresh output required')
gpath='work/frisc_graph_capture_2026-10-05/rr_graph.xml';g=read_rr_graph(gpath);oracle=TreeRC(g);inputs={gpath:sha(gpath)};results=[]
for label,predpath,reportpath in [('before','experiments/frisc_shared_trunk_gated_candidate_2026-10-05/prediction.json','experiments/frisc_shared_trunk_native_analysis_2026-10-05/report_timing.setup.rpt'),('after','experiments/frisc_shared_trunk_target_batch_2026-10-05/prediction.json','experiments/frisc_trunk_batch_native_analysis_2026-10-05/report_timing.setup.rpt')]:
 inputs[predpath]=sha(predpath);inputs[reportpath]=sha(reportpath);rows=[r for r in json.loads(Path(predpath).read_text())['connections'] if r['net_id']==49];tree=oracle.evaluate(rows[0]['source'],set(e for r in rows for e in r['physical_edge_ids']));lookup={}
 for row in rows:
  path=row['physical_edge_ids'];opin=g.edges[path[0]].sink;ipin=g.edges[path[-1]].source;lookup[(opin,ipin)]=row
 matches=[];block=[]
 for line in Path(reportpath).read_text().splitlines():
  m=re.match(r'^\| \((OPIN|IPIN|CHANX|CHANY):(\d+).*\)\s+([-0-9.]+)\s+([-0-9.]+)\s*$',line)
  if not m:continue
  kind,node,incr=m[1],int(m[2]),float(m[3])
  if kind=='OPIN':block=[]
  block.append((node,incr))
  if kind=='IPIN':
   key=(block[0][0],node);row=lookup.get(key)
   if row:
    expected_nodes=[g.edges[e].sink for e in row['physical_edge_ids'][:-1]];assert [n for n,_ in block]==expected_nodes;model=float(tree['delay_seconds'][node]*10**9);native=sum(v for _,v in block);bound=len(block)*0.0005+0.00001;matches.append({'cid':row['connection_id'],'model_ns':model,'printed_rr_delay_ns':native,'absolute_error_ns':abs(model-native),'rounding_bound_ns':bound,'within_report_precision':abs(model-native)<=bound})
   block=[]
 results.append({'label':label,'matched_report_segments':len(matches),'unique_cids':sorted({m['cid'] for m in matches}),'all_matched_within_report_precision':all(m['within_report_precision'] for m in matches),'matches':matches})
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());r={'results':results,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'only net49 segments present in top100 native setup reports; decimal metadata vs printed 3-decimal-ns increments, bounded rounding agreement is not exact float parity or whole-design STA validation'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='matches'} for r in results]))
