"""Evaluator-only exact net-ID/name/channel-span alignment over all nine routes."""
import json,re,time,argparse
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha,placements
from rr_graph import read_rr_graph
from feedback_scores import scores
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('experiments/frisc_native_span_cohort_2026-10-05'));args=parser.parse_args()
root=Path('experiments/frisc_native_candidate_labels_2026-10-05');out=args.output;epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json')
if out.exists():raise ValueError('fresh output required')
e=json.loads(epath.read_text());metrics=json.loads((root/'receipt.json').read_text());cohort={r['net_id'] for r in e['connections']};gentry=e['inputs']['graph'];assert sha(gentry['path'])==gentry['sha256'];start=time.monotonic();g=read_rr_graph(gentry['path']);inputs={str(epath):sha(epath),str(root/'receipt.json'):sha(root/'receipt.json'),gentry['path']:gentry['sha256']};rows=[]
for metric in metrics['rows']:
 cid=metric['candidate_id'];native=root/f'candidate_{cid}';receipt=json.loads((native/'receipt.json').read_text());protocol=json.loads((native/'protocol.json').read_text());assert protocol['inputs']['graph']['sha256']==g.sha256 and protocol['inputs']['net']['sha256']==e['inputs']['net']['sha256'];assert sha(native/'receipt.json')==metric['native_receipt_sha256']
 entry=receipt['final_route'];route=Path(entry['path']);place=route.with_suffix('.place');assert sha(route)==entry['sha256'];assert placements(place,e['inputs']['net']['sha256'])==placements(protocol['inputs']['place']['path'],e['inputs']['net']['sha256'])
 for path in (route,place,native/'receipt.json',native/'protocol.json'):inputs[str(path)]=sha(path)
 users={};net=None;names={};identity=False
 for line in route.read_text().splitlines():
  if line.startswith('Placement_File:'):
   match=re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',line);assert match and match[1]==sha(place);identity=True
  match=re.match(r'^\s*Net\s+(\d+)\s+\((.*)\)(?::.*)?\s*$',line)
  if match:
   net=int(match[1]);assert net not in users;users[net]=set();names[net]=match[2]
  match=re.match(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b',line)
  if match:
   n=int(match[1]);assert net is not None and g.nodes[n].type==match[2];users[net].add(n)
  elif line.lstrip().startswith('Node:'):raise ValueError('unparsed native node')
 assert identity and cohort<=users.keys()
 assert all(names[n]==e['net_names'][str(n)] for n in cohort)
 occupancy=Counter(n for net in cohort for n in users[net]);s=scores(g,e,occupancy)
 rows.append({'candidate_id':cid,'cohort_net_count':len(cohort),'excluded_native_net_count':len(users.keys()-cohort),'native_cohort_span':s['channel_net_span_sum'],'native_total_wirelength':metric['wirelength'],'same_value':s['channel_net_span_sum']==metric['wirelength'],'native_channel_overuse_units':s['predicted_channel_overuse_units']})
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());r={'rows':rows,'net_id_and_name_alignment_verified':True,'all_cohort_spans_equal_native_total_wirelength':all(x['same_value'] for x in rows),'input_sha256':inputs,'source_sha256':sha(__file__),'wall_s':time.monotonic()-start,'scope':'evaluator-only nine-route statistical cohort audit, no prediction tuning; not joint-tree legality proof'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'rows':rows,'all_equal':r['all_cohort_spans_equal_native_total_wirelength']}))
