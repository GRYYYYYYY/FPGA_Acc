"""No route or timing-label input: frozen packed/placed endpoint geometry."""
import json,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import extract,placements,sha
root=Path(__file__).resolve().parents[1];source=root/'work/native_candidate_timing_gate_2026-10-06/adder';out=root/'experiments/native_move_geometry_features_2026-10-06';out.mkdir();protocol=root/'experiments/native_candidate_common_state_2026-10-06/protocol.json';pairs=json.loads(protocol.read_text())['pairs'];graph=root/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml';start=time.perf_counter();endpoints,report=extract(source/'design.net',source/'design.place',graph);mapped=time.perf_counter();locs=placements(source/'design.place',sha(source/'design.net'));block_locs={v[4]:(v[0],v[1]) for v in locs.values()};net_blocks=defaultdict(set)
excluded={x['net'] for x in endpoints['excluded_nets']}
for pin in report['pin_details']:
 if pin['net'] not in excluded:net_blocks[pin['net']].add(pin['block_id'])
def hpwl(blocks,loc):
 points=[loc[b] for b in blocks];return max(x for x,y in points)-min(x for x,y in points)+max(y for x,y in points)-min(y for x,y in points)
rows=[]
for i,(a,b) in enumerate(pairs):
 moved=block_locs.copy();moved[a],moved[b]=moved[b],moved[a];dirty=[net for net,blocks in net_blocks.items() if a in blocks or b in blocks];delta=sum(hpwl(net_blocks[n],moved)-hpwl(net_blocks[n],block_locs) for n in dirty);rows.append({'index':i,'pair':[a,b],'dirty_nets':len(dirty),'delta_hpwl':delta,'selected_by_fixed_rule':delta<0})
finished=time.perf_counter();result={'pairs':rows,'cost_s':{'physical_mapping':mapped-start,'geometry_features':finished-mapped,'total':finished-start},'inputs_sha256':{str(p):sha(p) for p in (source/'design.net',source/'design.place',graph,protocol)},'source_sha256':sha(Path(__file__)),'fixed_rule':'Select only strictly negative aggregate NET HPWL change; no fitted weights or timing labels.','scope':'Geometry proxy on known designs, root clocks excluded, pure packed/place/RR mapping. Labels already exist elsewhere: retrospective evaluation, not independent prospective validation or RC delay prediction.'};(out/'features.json').write_text(json.dumps(result,indent=2)+'\n');print(result['cost_s']);print('selected',sum(x['selected_by_fixed_rule'] for x in rows),'of',len(rows))
