"""Evaluator-only same-cohort span diagnostic; never changes frozen policy."""
import json,re,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha,placements
from rr_graph import read_rr_graph
from feedback_scores import scores

out=Path('experiments/elliptic_matched_span_diagnostic_2026-10-05')
if out.exists():raise ValueError('fresh output required')
start=time.monotonic(); root=Path('experiments/elliptic_prospective_feedback_2026-10-05')
epath=Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json');e=json.loads(epath.read_text());decision=json.loads((root/'decision.json').read_text())
assert decision['selected_candidate']==6
inputs={str(epath):sha(epath),str(root/'decision.json'):sha(root/'decision.json')}
gentry=e['inputs']['graph'];assert sha(gentry['path'])==gentry['sha256'];inputs[gentry['path']]=gentry['sha256']
g=read_rr_graph(gentry['path']);cohort={r['net_id'] for r in e['connections']}
base=json.loads(Path('experiments/elliptic_graph_capture_2026-10-04/receipt.json').read_text())
selected=json.loads((root/'selected_native/receipt.json').read_text());protocol=json.loads((root/'selected_native/protocol.json').read_text())
native_place=Path(selected['final_route']['path']).with_suffix('.place')
assert placements(native_place,e['inputs']['net']['sha256'])==placements(protocol['inputs']['place']['path'],e['inputs']['net']['sha256'])
inputs[str(native_place)]=sha(native_place);inputs[protocol['inputs']['place']['path']]=protocol['inputs']['place']['sha256']
entries=[(base['artifacts']['elliptic.route'],e['inputs']['place']['sha256']),(selected['final_route'],sha(native_place))]
rows=[]
for label,(entry,place_sha) in zip(('baseline','candidate_6'),entries):
 assert sha(entry['path'])==entry['sha256'];inputs[entry['path']]=entry['sha256']
 unions={};net=None;identity=False
 for line in Path(entry['path']).read_text().splitlines():
  if line.startswith('Placement_File:'):
   match=re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',line);assert match and match[1]==place_sha;identity=True
  match=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
  if match:
   net=int(match[1]);assert net not in unions;unions[net]=set()
  match=re.match(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b',line)
  if match:
   n=int(match[1]);assert net is not None and g.nodes[n].type==match[2];unions[net].add(n)
  elif line.lstrip().startswith('Node:'):raise ValueError('unparsed node')
 assert identity and cohort<=unions.keys()
 occupancy=Counter(n for net in cohort for n in unions[net]);s=scores(g,e,occupancy)
 rows.append({'label':label,'cohort_net_count':len(cohort),'native_channel_net_span_sum':s['channel_net_span_sum'],'native_overuse_units':s['predicted_channel_overuse_units'],'excluded_net_count':len(unions.keys()-cohort)})
pred={r['candidate_id']:r for r in decision['scores']};pd=pred[6]['channel_net_span_sum']-pred[0]['channel_net_span_sum'];nd=rows[1]['native_channel_net_span_sum']-rows[0]['native_channel_net_span_sum']
assert all(sha(p)==s for p,s in inputs.items())
receipt={'scope':'posthoc same graph, same endpoint-net cohort, same unique-net channel span formula; diagnostic only, no policy tuning','source_sha256':sha(__file__),'input_sha256':inputs,'native_rows':rows,'predicted_baseline_span':pred[0]['channel_net_span_sum'],'predicted_candidate_span':pred[6]['channel_net_span_sum'],'predicted_span_delta':pd,'native_matched_span_delta':nd,'direction_disagreement':pd*nd<0,'limitations':['one previously explored design','native routes differ from independent sketch connection paths','does not establish root cause or unseen-family generalization'],'wall_s':time.monotonic()-start}
out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
