"""Independent full-state affected-net selection, retained paths and scoring."""
import json
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_swap_decision_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
P=E/'full_ram_swap_incremental_v1_2026-10-09';C=E/'full_ram_swap_candidates_v1_2026-10-09';B=E/'full_ram_length_switch_prediction_v1_2026-10-09';epfile=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json';graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
r=json.loads((P/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_INCREMENTAL_DECISION'
for p,h in r['bindings'].items():assert sha(p)==h
g=read_rr_graph(graph);old=json.loads(epfile.read_text());bg=json.loads((B/'prediction.json').read_text());oldrows={c['connection_id']:c for c in old['connections']};oldpaths={c['connection_id']:c['physical_edge_ids'] for c in bg['connections']};reports=[];paths=[Path(__file__),P/'receipt.json',graph,epfile,B/'prediction.json']
def independent_scores(ep,pred):
 span=over=0
 for n,v in pred['node_occupancy'].items():
  node=g.nodes[int(n)]
  if node.type in ('CHANX','CHANY'):
   loc=dict(node.location);span+=v*(max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1);over+=max(0,v-node.capacity)
 points=defaultdict(list)
 for c in ep['connections']:
  for n in (c['source'],c['sink']):
   loc=dict(g.nodes[n].location);points[c['net_id']].append((int(loc['xlow']),int(loc['ylow'])))
 hpwl=sum(max(x for x,y in ns)-min(x for x,y in ns)+max(y for x,y in ns)-min(y for x,y in ns) for ns in points.values())
 return dict(channel_net_span_sum=span,predicted_channel_overuse_units=over,net_bbox_hpwl=hpwl)
for cid in (0,1,2):
 if cid==0:ep=old;pred=bg;selected=set();updated=0
 else:
  ep_path=C/f'candidate_{cid}/endpoints.json';pred_path=P/f'candidate_{cid}/prediction.json';paths.extend([ep_path,pred_path]);ep=json.loads(ep_path.read_text());pred=json.loads(pred_path.read_text())
  selected={c['net_id'] for c in ep['connections'] if (c['source'],c['sink'])!=(oldrows[c['connection_id']]['source'],oldrows[c['connection_id']]['sink'])}
  journal={x['net_id']:x['result'] for x in map(json.loads,(P/f'candidate_{cid}/net_results.jsonl').read_text().splitlines())};assert set(journal)==selected;updated=0
  for c in pred['connections']:
   if c['net_id'] in selected:assert c['physical_edge_ids']==journal[c['net_id']]['paths'][str(c['sink'])];updated+=1
   else:assert c['physical_edge_ids']==oldpaths[c['connection_id']]
 checked=audit(g,ep,pred);score=independent_scores(ep,pred);prior=r['details']['reports'][cid];assert score==prior['scores']
 if cid:assert updated==prior['recomputed_connections'] and len(selected)==prior['affected_nets']
 reports.append(dict(candidate=cid,scores=score,updated_connections=updated,affected_nets=len(selected),audit=checked))
selected=min(reports,key=lambda x:(x['scores']['channel_net_span_sum'],x['scores']['predicted_channel_overuse_units'],x['candidate']))['candidate'];assert selected==r['details']['selected_candidate']
(D/'verification.json').write_text(json.dumps(dict(passed=True,reports=reports,selected_candidate=selected,bindings={str(p):sha(p) for p in paths},scope='Independent selection/retained-path/journal reconstruction/full physical occupancy/score arithmetic. Does not prove new-query shortest-path optimality or native joint legality.'),indent=2)+'\n');print('PASS',selected,[(x['candidate'],x['updated_connections']) for x in reports])
