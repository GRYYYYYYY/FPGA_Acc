"""Authenticated same-setting native comparison and exported path round trip."""
import json,re,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
start=time.monotonic();out=Path('experiments/frisc_budget_cohort_native_comparison_2026-10-05')
if out.exists():raise ValueError('fresh output required')
roots=[Path('experiments/frisc_zero_channel_baseline_analysis_2026-10-05'),Path('experiments/frisc_budget_cohort_native_analysis_2026-10-05')];metrics=[];protocols=[];inputs={}
for root in roots:
 protocol=json.loads((root/'protocol.json').read_text());receipt=json.loads((root/'receipt.json').read_text());assert receipt['exit_code']==0 and not receipt['timed_out'] and receipt['input_hashes_unchanged'] and receipt['copied_route_unchanged'];assert sha(root/'protocol.json')==receipt['protocol_sha256'] and sha(root/'stdout.txt')==receipt['stdout_sha256'];assert all(sha(v['path'])==v['sha256'] for v in protocol['inputs'].values());text=(root/'stdout.txt').read_text();assert 'RouterOpts.check_route: FULL' in text and 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text and 'analysis results are for an illegal' not in text
 post=Path(protocol['cwd'])/'frisc.net.post_routing';assert post.exists();inputs[str(post)]=sha(post)
 metrics.append({'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1]),'analysis_wall_s':receipt['wall_s'],'full_native_route_check_passed':True,'post_routing_packing_sha256':sha(post)});protocols.append(protocol)
 for f in ('protocol.json','receipt.json','stdout.txt'):inputs[str(root/f)]=sha(root/f)
assert protocols[0]['command']==protocols[1]['command'];assert all(protocols[0]['inputs'][key]==protocols[1]['inputs'][key] for key in ('vpr','arch','blif','net','place','graph'))
export=Path('experiments/frisc_budget_cohort_route_export_2026-10-05');mapping=json.loads((export/'mapping.json').read_text());predpath=Path('experiments/frisc_incremental_budget_cohort_2026-10-05/prediction.json');pred=json.loads(predpath.read_text());g=read_rr_graph(protocols[1]['inputs']['graph']['path']);expected={r['connection_id']:[(g.edges[e].source,g.edges[e].sink,g.edges[e].switch_id) for e in r['physical_edge_ids']] for r in pred['connections']};lookup={(r['native_net_name'],r['native_net_pin_index']):r['connection_id'] for r in mapping};assert len(lookup)==len(expected);seen=set();parents={};name=None;previous=None;switch=None;printed_union={};used=set()
for line in (export/'frisc.route').read_text().splitlines():
 m=re.match(r'Net \d+ \((.*)\)',line)
 if m:
  if name is not None:printed_union[name]=used
  name=m[1];parents={};previous=None;switch=None;used=set();continue
 m=re.match(r'Node:\s*(\d+)\s+(\w+).*Switch:\s*(-?\d+)(?: Net_pin_index:\s*(\d+))?',line)
 if not m:continue
 node=int(m[1]);kind=m[2];used.add(node)
 if kind=='SOURCE':parents[node]=None
 elif node not in parents:parents[node]=(previous,switch)
 if kind=='SINK':
  index=int(m[4]);cid=lookup[(name,index)];assert cid not in seen;seen.add(cid);edges=[];cursor=node
  while parents[cursor] is not None:
   parent,arc_switch=parents[cursor];edges.append((parent,cursor,arc_switch));cursor=parent
  assert list(reversed(edges))==expected[cid]
 previous=node;switch=int(m[3])
if name is not None:printed_union[name]=used
assert seen==set(expected)
# Exported routed unions agree exactly with predictor occupancy, not merely score.
demand=Counter(n for nodes in printed_union.values() for n in nodes);assert {str(n):v for n,v in demand.items()}==pred['node_occupancy']
for path in (predpath,export/'mapping.json',export/'frisc.route'):inputs[str(path)]=sha(path)
a,b=metrics;delta={'wirelength':b['wirelength']-a['wirelength'],'wirelength_percent':100*(b['wirelength']/a['wirelength']-1),'cpd_ns':b['cpd_ns']-a['cpd_ns'],'cpd_percent':100*(b['cpd_ns']/a['cpd_ns']-1)}
out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());r={'baseline':a,'routecast':b,'delta':delta,'same_native_command_and_nonroute_inputs':True,'round_trip_all_connection_paths_exact':len(seen),'round_trip_unique_net_occupancy_exact':True,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'full_wall_s':time.monotonic()-start,'scope':'legal native full-check/packed resync/STA on one developed frisc instance; wirelength and timing worsen, no unseen-family or end-to-end speed evidence'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
