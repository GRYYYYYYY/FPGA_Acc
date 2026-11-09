"""Evaluator-only span/sharing and STA rank diagnostics; no candidate generation."""
import json,re,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
start=time.monotonic();out=Path('experiments/frisc_zero_channel_regression_diagnostic_2026-10-05')
if out.exists():raise ValueError('fresh output required')
gpath='work/frisc_graph_capture_2026-10-05/rr_graph.xml';epath='experiments/frisc_endpoints_2026-10-05/endpoints.json';inputs={p:sha(p) for p in (gpath,epath)};g=read_rr_graph(gpath);e=json.loads(Path(epath).read_text());names={v:int(k) for k,v in e['net_names'].items()};active={r['net_id'] for r in e['connections']}
def channelspan(n):
 node=g.nodes[n]
 if node.type not in {'CHANX','CHANY'}:return 0
 loc=dict(node.location);return max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
span={n:channelspan(n) for n in g.nodes};stages={}
files={'initial_sketch':'experiments/frisc_timing_backgrounds_v2_2026-10-05/baseline_prediction.json','simultaneous_pin_repair':'experiments/frisc_full_weighted_pin_commit_2026-10-05/prediction.json','compatible_round4':'experiments/frisc_sequential_pin_compatible_round4_2026-10-05/prediction.json','zero_channel':'experiments/frisc_final_one_candidate_commit_2026-10-05/prediction.json'}
for label,path in files.items():
 inputs[path]=sha(path);p=json.loads(Path(path).read_text());assert p['physical_graph_sha256']==g.sha256;unions=defaultdict(set);total=Counter();count=Counter()
 for r in p['connections']:
  nodes=[r['source']]+[g.edges[a].sink for a in r['physical_edge_ids']];assert len(set(nodes))==len(nodes);unions[r['net_id']].update(nodes);total[r['net_id']]+=sum(span[n] for n in nodes);count[r['net_id']]+=1
 demand=Counter(n for nodes in unions.values() for n in nodes);assert {str(n):v for n,v in demand.items()}==p['node_occupancy'];assert set(unions)==active
 stages[label]={net:{'union_span':sum(span[n] for n in unions[net]),'sum_connection_spans':total[net],'connections':count[net]} for net in sorted(active)}
routepath='work/frisc_graph_capture_2026-10-05/frisc.route';inputs[routepath]=sha(routepath);native={};net=None;parents={};used=set();total=0;count=0;previous=None
def finish():
 if net in active:native[net]={'union_span':sum(span[n] for n in used),'sum_connection_spans':total,'connections':count}
for line in Path(routepath).read_text().splitlines():
 m=re.match(r'^Net \d+ \((.*?)\)(.*)$',line)
 if m:finish();net=names[m[1]];parents={};used=set();total=0;count=0;previous=None;continue
 m=re.match(r'Node:\s*(\d+)\s+(\w+)',line)
 if not m:continue
 node=int(m[1]);kind=m[2];used.add(node)
 if kind=='SOURCE':parents[node]=None
 elif node not in parents:parents[node]=previous
 if kind=='SINK':
  count+=1;cursor=node
  while cursor is not None:total+=span[cursor];cursor=parents[cursor]
 previous=node
finish();assert set(native)==active;stages={'native_baseline':native,**stages}
aggregates={label:{'union_span':sum(r['union_span'] for r in data.values()),'sum_connection_spans':sum(r['sum_connection_spans'] for r in data.values()),'connections':sum(r['connections'] for r in data.values())} for label,data in stages.items()}
assert aggregates['native_baseline']['union_span']==33182 and aggregates['zero_channel']['union_span']==46235
rows=[{'net_id':net,'name':e['net_names'][str(net)],'connections':native[net]['connections'],'stages':{label:stage[net] for label,stage in stages.items()},'final_vs_native_delta':stages['zero_channel'][net]['union_span']-native[net]['union_span'],'pin_repair_delta':stages['simultaneous_pin_repair'][net]['union_span']-stages['initial_sketch'][net]['union_span']} for net in sorted(active)]
ordered=sorted(rows,key=lambda r:(-r['final_vs_native_delta'],r['net_id']));positive=sum(max(0,r['final_vs_native_delta']) for r in rows);negative=sum(min(0,r['final_vs_native_delta']) for r in rows)
reports={};timing=[]
for label in ('baseline','native'):
 path=f'experiments/frisc_zero_channel_{label}_analysis_2026-10-05/report_timing.setup.rpt';inputs[path]=sha(path);paths=[]
 for chunk in re.split(r'(?m)^#Path ',Path(path).read_text())[1:]:
  rank=int(chunk.splitlines()[0]);source=re.search(r'^Startpoint: (.*)',chunk,re.M)[1];sink=re.search(r'^Endpoint\s*: (.*)',chunk,re.M)[1];arrival=float(re.search(r'^data arrival time\s+([-0-9.]+)',chunk,re.M)[1]);slack=float(re.search(r'^slack \(\w+\)\s+([-0-9.]+)',chunk,re.M)[1]);rr=[int(n) for n in re.findall(r'\| \((?:OPIN|IPIN|CHANX|CHANY):(\d+)',chunk)];paths.append({'rank':rank,'startpoint':source,'endpoint':sink,'arrival_ns':arrival,'slack_ns':slack,'rr_nodes':rr})
 reports[label]=paths
index={(r['startpoint'],r['endpoint']):r for r in reports['baseline']}
for r in reports['native']:
 old=index.get((r['startpoint'],r['endpoint']));timing.append({'native_rank':r['rank'],'startpoint':r['startpoint'],'endpoint':r['endpoint'],'baseline_rank':old['rank'] if old else None,'arrival_delta_ns':r['arrival_ns']-old['arrival_ns'] if old else None,'slack_delta_ns':r['slack_ns']-old['slack_ns'] if old else None,'rr_sequence_equal':r['rr_nodes']==old['rr_nodes'] if old else None})
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'net_rows.json').write_text(json.dumps(rows)+'\n');(out/'timing_paths.json').write_text(json.dumps({'reports':reports,'matched':timing})+'\n');r={'aggregates':aggregates,'positive_net_delta':positive,'negative_net_delta':negative,'final_vs_native_net_counts':dict(Counter('longer' if r['final_vs_native_delta']>0 else 'shorter' if r['final_vs_native_delta']<0 else 'equal' for r in rows)),'top20_positive_net_delta':sum(max(0,r['final_vs_native_delta']) for r in ordered[:20]),'top20_nets':[r['net_id'] for r in ordered[:20]],'timing_top100_matched_endpoint_pairs':sum(r['baseline_rank'] is not None for r in timing),'worst_baseline_path':reports['baseline'][0],'worst_routecast_path':reports['native'][0],'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'full_wall_s':time.monotonic()-start,'scope':'posthoc stage accounting and STA endpoint matching; ranks and shared-trunk ratios do not establish causality or prospective optimization policy'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('worst_baseline_path','worst_routecast_path','input_sha256')}))
