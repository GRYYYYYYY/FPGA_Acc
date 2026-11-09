"""Full fixed development cohort comparison; all types/metrics retained."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/freecores_segment_delay_pool_comparison_v1_2026-10-08';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
def read(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
def proof(path,flag):
 d=read(path);assert d[flag] and all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
receipt=read(R/'experiments/freecores_segment_delay_pool_model_v1_2026-10-08/receipt.json');assert all(sha(k)==h for k,h in receipt['bindings'].items());assert [x['name'] for x in receipt['rows']]==['8051','xtea'] and all(x['status']=='COMPLETE_INITIAL_FINAL_EVENT_AUDIT_PASS' and all(sha(k)==h for k,h in x['files'].items()) for x in receipt['rows'])
for name in ['8051','xtea']:
 graph=R/'experiments/freecores_rr_only_v1_2026-10-08'/name/'rr_graph.xml';bindings[str(graph)]=sha(graph);types={};caps={};stack=[]
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if el.tag=='node' and parent=='rr_nodes':nid=int(el.get('id'));types[nid]=el.get('type');caps[nid]=int(el.get('capacity'))
  if (el.tag,parent) in {('node','rr_nodes'),('edge','rr_edges'),('switch','switches')}:stack[-2].remove(el);el.clear()
  stack.pop()
 methods={}
 for mode in ['baseline','segment_delay_pool_dynamic_price']:
  base=R/('experiments/freecores_resident_v1_2026-10-08' if mode=='baseline' else 'experiments/freecores_segment_delay_pool_model_v1_2026-10-08')/name/'resident'
  vp=proof(base/'verification.json','complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass');frames={}
  for frame in ['initial','sketch']:
   proof(base/(frame+'_physical_verification.json'),'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass');c=read(base/(frame+'.json'));units=Counter();nodes=Counter();allcounts=Counter()
   for nid,count in c['ledger'].items():
    n=int(nid);assert caps[n]>0;allcounts[types[n]]+=count
    if count>caps[n]:units[types[n]]+=count-caps[n];nodes[types[n]]+=1
   assert sum(units.values())==c['overflow_units'];frames[frame]=dict(overuse_units_by_type=dict(units),overused_nodes_by_type=dict(nodes),unique_NET_occupancy_sum_by_type=dict(allcounts),total_overuse_units=c['overflow_units'])
  metricbase=R/('experiments/freecores_hotspots_v1_2026-10-08' if mode=='baseline' else 'experiments/freecores_segment_delay_pool_hotspots_v1_2026-10-08')/name;mp=proof(metricbase/'metric_verification.json','histogram_ranks_topk_mae_and_full_vector_scope_pass');assert mp['metric_vectors_recomputed']==7;metric=read(metricbase/'comparison.json');methods[mode]=dict(frames=frames,events=vp['events'],committed=vp['committed'],retained=vp['retained'],metrics=metric['metrics'])
  if mode=='segment_delay_pool_dynamic_price':
   protocol=read(base/'protocol.json');assert protocol['feedback_objective']=='Channel entry full electrical objective pooled by source type,target orientation,target polarity across segment IDs; original raw RC unchanged'
   component=proof(R/'experiments/freecores_segment_delay_pool_v1_2026-10-08'/name/'verification.json','all_original_XML_raw_arcs_unchanged_and_pooled_objective_exact_pass');assert component['changed_objective_arcs']>0
 assert methods['baseline']['frames']['initial']==methods['segment_delay_pool_dynamic_price']['frames']['initial'];rows.append(dict(name=name,methods=methods));print(name,'FULL PRICE TYPE + METRIC COMPARISON PASS',flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_complete_cases_types_and_14_metric_vectors_authenticated=True,scope='Development knockout of existing baseline segment electrical distinctions; original cold labels already observed. All cases/types/baselines/metric outcomes retained, no case/price selection, no native RRR/timing gain/strict-heldout/HDL/real async timing proof.'),indent=2)+'\n')
