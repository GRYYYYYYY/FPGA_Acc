"""Map exposed development swap layouts to exact SOURCE/SINK RR classes."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import PhysicalMapContext,extract,sha

def main():
 seed=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed';net=seed/'demand/mmc/design.net';graph=seed/'rr/mmc/rr_graph.xml';prior=R/'experiments/prospective_layout_swap_real_MMC_v1_2026-10-18/verification.json';p=json.loads(prior.read_text())
 for path,h in p['bindings'].items():assert sha(path)==h
 out=R/'experiments/prospective_layout_swap_endpoints_v2_2026-10-18';out.mkdir(exist_ok=False);bindings={str(x):sha(x) for x in [Path(__file__),R/'tools/pre_route_endpoints.py',prior,net,graph]};start=time.perf_counter();context=PhysicalMapContext(graph);print('PHYSICAL CONTEXT READY',flush=True);rows=[]
 for episode in p['episodes']:
  place=Path(episode['file']);assert sha(place)==episode['sha256'];tick=time.perf_counter();endpoints,report=extract(net,place,graph,physical_context=context);assert len(endpoints['connections'])==115973
  ep=out/f'episode_{episode["episode"]:02}';ep.mkdir();a=ep/'endpoints.json';b=ep/'mapping.json';a.write_text(json.dumps(endpoints,separators=(',',':')));b.write_text(json.dumps(report,separators=(',',':')))
  baseline=json.loads((seed/'rr/mmc/endpoints.json').read_text());assert [(c['connection_id'],c['net_id']) for c in endpoints['connections']]==[(c['connection_id'],c['net_id']) for c in baseline['connections']];assert endpoints['net_names']==baseline['net_names']
  rows.append(dict(episode=episode['episode'],placement=str(place),placement_sha256=sha(place),connections=len(endpoints['connections']),pins=len(report['pin_details']),endpoints=str(a),endpoints_sha256=sha(a),mapping=str(b),mapping_sha256=sha(b),component_seconds=time.perf_counter()-tick));print('EPISODE MAPPED',episode['episode'],len(endpoints['connections']),flush=True)
 for path,h in bindings.items():assert sha(path)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='three_development_swap_layouts_all_pins_mapped_to_exact_RR_classes',bindings=bindings,episodes=rows,component_seconds=time.perf_counter()-start,scope='Pre-route pin-class extraction for exposed MMC development geometry. Explicit root clocks excluded; all115973raw nonclock physical connections retained; native ignored-connection filtering is not applied here. Does not prove native acceptance, route existence, independent timing, model quality or strict-family admission. No route or prediction generated.'),f,indent=2)
 print('ENDPOINT MAPPING TERMINAL PASS',flush=True)
if __name__=='__main__':main()
