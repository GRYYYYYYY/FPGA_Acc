"""Separate fixed three-round native occupancy evaluation and cost accounting."""
from pathlib import Path
import json,shutil
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
parent=Path('experiments/q8_pressure_rounds_2026-10-04');out=Path('experiments/q8_pressure_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());assert receipt['protocol_sha256']==sha(parent/'protocol.json')
for n,digest in receipt['artifacts'].items():assert sha(parent/n)==digest
previous_eval=Path('experiments/frozen_pressure_evaluation_2026-10-04');lp=json.loads((previous_eval/'protocol.json').read_text());old=json.loads((previous_eval/'receipt.json').read_text());assert old['protocol_sha256']==sha(previous_eval/'protocol.json')
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'scope':'Q8 half damping control; same alpha/3rounds, compare integer damping and undamped, no retrospective selection or generalization claim','predictor_protocol_sha256':sha(parent/'protocol.json'),'labels':lp['labels'],'primary':'round3 terminal accuracy/overflows, adjacent demand L1; compare undamped same cohort; quantify integer-ceil bias','prior_evaluation_receipt_sha256':sha(previous_eval/'receipt.json'),'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
protocol['integer_damped_receipt_sha256']=sha('experiments/damped_pressure_evaluation_2026-10-04/receipt.json')
protocol['undamped_receipt_sha256']=sha('experiments/pressure_rounds_evaluation_2026-10-04/receipt.json')
protocol['background_cost_receipts']={f:sha(f) for f in ('experiments/pressure_background_cost_2026-10-04/receipt.json','experiments/elliptic_transfer_2026-10-04/receipt.json')}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results={}
first_receipt=json.loads(Path('experiments/frozen_pressure_2026-10-04/receipt.json').read_text());background_receipt=json.loads(Path('experiments/elliptic_transfer_2026-10-04/receipt.json').read_text())
for name,paths in p['inputs'].items():
    for entry in paths.values():assert sha(entry['path'])==entry['sha256']
    label=protocol['labels'][name];assert sha(label['route'])==label['route_sha256'];g=read_rr_graph(paths['graph']['path']);truth=node_labels(g,label['route'],label['place_sha256']);resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];rows={'zero':old['results'][name]['zero'],'round1':old['results'][name]['pressure']}
    for round_id in (2,3):
        pred=json.loads((parent/f'{name}_round{round_id}.json').read_text());assert pred['physical_graph_sha256']==g.sha256;values=pred['node_occupancy'];rows[f'round{round_id}']={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_nodes':sum(v>g.nodes[int(n)].capacity for n,v in values.items()),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items())}
    extra=[v for v in receipt['reports'] if v['design']==name];first=next(v for v in first_receipt['reports'] if v['design']==name)
    measured=first['preparation_wall_s']+first['search_and_ledger_wall_s']+extra[0]['graph_load_wall_s_once']+sum(v['index_prepare_s']+v['search_ledger_s'] for v in extra)
    bg=sum(background_receipt[k] for k in ('load_wall_s','construct_wall_s','repair_wall_s')) if name=='elliptic' else json.loads(Path('experiments/pressure_background_cost_2026-10-04/receipt.json').read_text())['background_acquisition_s']
    undamped=json.loads(Path('experiments/pressure_rounds_evaluation_2026-10-04/receipt.json').read_text())['results'][name]
    results[name]={'integer_damped_accuracy':json.loads(Path('experiments/damped_pressure_evaluation_2026-10-04/receipt.json').read_text())['results'][name]['accuracy'],'undamped_accuracy':undamped['accuracy'],'undamped_oscillation':undamped['oscillation'],'accuracy':rows,'oscillation':extra,'staged_observed_pressure_cost_s':measured,'background_prediction_acquisition_observed_s':bg,'background_cost_note':'separately measured exact background stages counted; not same-run total','historical_background_plus_pressure_stage_sum_s':None if bg is None else bg+measured}
    print(json.dumps({'design':name,'resource_spearman':{k:v['resource']['spearman'] for k,v in rows.items()},'pressure_stage_s':measured,'background_s':bg}),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results},indent=2)+'\n')
