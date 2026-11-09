import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_feedback_round_ablation_v1_2026-10-08';p=out/'span_control_NET_owner_diagnosis.json';d=json.loads(p.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))}
for file in ['comparison.json','metric_verification.json','vector_verification.json']:
 p=out/file;x=json.loads(p.read_text());assert all(sha(k)==v for k,v in x['bindings'].items());bindings[str(p)]=sha(p)
metrics={x['name']:x['metrics'] for x in json.loads((out/'comparison.json').read_text())['rows']};rows=[]
for row in d['rows']:
 states={};nodes=row['all_top20_node_owners'];assert len({n['node'] for n in nodes})==len(nodes)==row['physical_support_nodes']
 for frame in ['initial','span_round0','span_round1','no_span_round0','no_span_round1']:
  common=missing=extra=0
  for node in nodes:
   native=set(node['native_owners']);s=node['frames'][frame];pred=set(s['predicted_owners']);assert len(native)==len(node['native_owners']) and len(pred)==len(s['predicted_owners']);assert set(s['common'])==native&pred and set(s['missing'])==native-pred and set(s['extra'])==pred-native
   common+=len(native&pred);missing+=len(native-pred);extra+=len(pred-native)
  states[frame]=dict(common_NET_node_pairs=common,missing_NET_node_pairs=missing,extra_NET_node_pairs=extra,owner_pair_recall=common/(common+missing),owner_pair_precision=common/(common+extra))
 groups=[]
 for g in row['repeated_support_group_NETs']:
  nset=set(g['native_NETs']);gs={}
  for frame,s in g['frames'].items():
   pset=set(s['predicted_NETs']);assert set(s['common_NETs'])==nset&pset and {x['name'] for x in s['missing_NETs']}==nset-pset and set(s['extra_NETs'])==pset-nset
   gs[frame]=dict(native_NETs=len(nset),predicted_NETs=len(pset),common_NETs=len(nset&pset),missing_NETs=len(nset-pset),extra_NETs=len(pset-nset))
  groups.append(dict(keys=g['keys'],states=gs))
 rows.append(dict(name=row['name'],all_true_top20_support_owner_pairs=states,repeated_support_groups=groups,full_universe_spatial_metrics={m:metrics[row['name']][m]['spatial'] for m in ['wire_shared','no_span_shared']}))
assert all(sha(k)==v for k,v in bindings.items())
(out/'span_control_owner_comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Set partition and aggregate checks on all true-top20 support nodes, plus authenticated full-universe descriptive metrics. No heldout claim or new model/parameter decision. Pair overlap is not route legality or native QoR.'),indent=2)+'\n')
for r in rows:print(r['name'],r['repeated_support_groups'],{m:(v['spearman'],v['precision_at_k']) for m,v in r['full_universe_spatial_metrics'].items()})
