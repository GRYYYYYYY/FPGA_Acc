"""Runtime parameter/source matrix and graph-specific inactive mismatch checks."""
import json,re,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src';D=E/'wbuart_native_model_cost_semantics_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';files=[Path(__file__),W,R/'RESEARCH_PLAN.md',R/'tools/compiled_criticality_tree_v1.py',R/'tools/criticality_retained_net_primary_v1.py',R/'tools/multiplicative_occupancy_context_v1.py',V/'route/connection_router.cpp',V/'route/route_net.cpp',V/'route/route_common.h',V/'route/route.cpp',V/'base/read_options.cpp'];bindings={str(p):sha(p) for p in files};graphs={};rows=[]
 for c in read(W)['comparisons']:
  s=read(c['specification']);ep=read(s['endpoint']);g=ep['inputs']['graph']['path'];width=c['case'].split('/')[0];baseproof=E/'wbuart_node_bases_v1_2026-10-20'/width/'verification.json';b=read(baseproof);assert b['all_native_T_quadratic_zero'] and b['all_native_base_equal_saved'];assert all(sha(p)==h for p,h in b['bindings'].items());log=Path(s['label_physical_audit']).parent/'native.log';text=log.read_text();options={name:float(re.search(r'RouterOpts\.'+name+r':\s*([0-9.eE+-]+)',text)[1]) for name in ['first_iter_pres_fac','initial_pres_fac','pres_fac_mult','acc_fac','bend_cost','bb_factor']};assert options['first_iter_pres_fac']==0 and options['initial_pres_fac']==.5 and options['acc_fac']==1 and options['bend_cost']==0
  if g not in graphs:
   kinds=[];edges=[];switch_types=[]
   for _,node in ET.iterparse(g):
    if node.tag=='node' and node.get('capacity') is not None:assert int(node.get('id'))==len(kinds);kinds.append(node.get('type'))
    elif node.tag=='edge':edges.append((int(node.get('src_node')),int(node.get('sink_node'))))
    elif node.tag=='switch':switch_types.append(node.get('type'))
   outgoing=defaultdict(set)
   for u,v in edges:outgoing[u].add(v)
   assert all(t=='mux' for t in switch_types);assert all(not outgoing[n] for n,k in enumerate(kinds) if k=='SINK');assert all(kinds[v]=='SINK' for n,k in enumerate(kinds) if k=='IPIN' for v in outgoing[n]);graphs[g]=(kinds,outgoing);bindings[g]=sha(g)
  kinds,outgoing=graphs[g];forecast=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json');arm=next(a for r in forecast['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated');q_by_net=defaultdict(set)
  for q in ep['connections']:q_by_net[q['net_id']].add(q['sink'])
  possible_terminal_crossreach=0;states=[Path(arm['output'])/name for name in ['initial.json','round0.json','round1.json']]
  for p in states:
   used=defaultdict(set)
   for q in read(p)['records']:
    # Native graph IPIN exits only into SINK; infer actual IPIN seed ownership from edge destinations.
    used[q['net_id']].add(q['sink'])
   # All routed sinks in a complete NET seed already belong to settled connections.
   for net,sinks in used.items():assert sinks==q_by_net[net]
  rows.append({'case':c['case'],'runtime_native_options':options,'model_present_factors':[1,1],'native_first_two_present_factors':[options['first_iter_pres_fac'],options['initial_pres_fac']],'fanout_base_scaling_inactive_Tquadratic_zero':True,'all_graph_switches_mux':True,'SINK_has_no_outgoing_edges_and_IPIN_exits_only_to_SINK':True,'terminal_seed_cross_target_impact_fully_verified':False,'terminal_seed_scope':'Topology narrows possible impact; full candidate seed-IPIN→other unsettled SINK membership not yet checked, do not declare complete equivalence.'});print(c['case'],options,flush=True)
  for p in [baseproof,log,*states]:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_RUNTIME_NATIVE_PRESSURE_SCHEDULE_AND_MODEL_SOURCE_DIFFERENCES_AUDITED','rows':rows,'bindings':bindings,'scope':'Runtime factors verified, source branch/tree seeding and group objective differences recorded. No source/mismatch count proves prediction causality or native equivalence. Static span removal already failed historical MMC evidence; no blind repetition. IPIN seed cross-target effect not fully certified.'},indent=2)+'\n')
if __name__=='__main__':main()
