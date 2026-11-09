"""Evaluate revised conv_layer baseline only after physical witness audit."""
import json,time,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import compare
from stream_metric_domain import metric_domain

def run():
    base=Path('experiments');parent=base/'conv_layer_length_switch_bbox3_prediction_2026-10-06';native=base/'conv_layer_native_route_labels_audit_v2_2026-10-06'
    physical=Path(str(parent)+'_physical_audit');out=base/'conv_layer_bbox3_evaluation_2026-10-06'
    if out.exists():raise ValueError('fresh output required')
    p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text())
    nr=json.loads((native/'receipt.json').read_text());ar=json.loads((physical/'receipt.json').read_text())
    assert r['protocol_sha256']==sha(parent/'protocol.json')
    assert ar['prediction_receipt_sha256']==sha(parent/'receipt.json')
    assert ar['protocol_sha256']==sha(physical/'protocol.json')
    ap=json.loads((physical/'protocol.json').read_text())
    assert ar['result']['all_physical_and_union_checks_passed']
    assert ar['result']['requested']==21140
    assert nr['protocol_sha256']==sha(native/'protocol.json')
    assert nr['physical_checks_pass']
    np=json.loads((native/'protocol.json').read_text())
    assert all(sha(v['path'])==v['sha256'] for v in np['inputs'].values())
    assert all(sha(native/'source'/n)==h for n,h in np['source_sha256'].items())
    assert np['inputs']['graph']==p['inputs']['graph'] and np['inputs']['endpoints']==p['inputs']['endpoints']
    assert np['frontend_receipt_sha256']==p['frontend_receipt_sha256']
    alignment_root=base/'conv_layer_native_endpoint_alignment_v2_2026-10-06'
    alignment_protocol=json.loads((alignment_root/'protocol.json').read_text())
    paths={'prediction':parent/'prediction.json','native':native/'physical_branches.json',
           'alignment':base/'conv_layer_native_endpoint_alignment_v2_2026-10-06/receipt.json'}
    inputs={k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()}
    inputs.update({k:p['inputs'][k] for k in ('graph','endpoints')})
    assert inputs['prediction']['sha256']==r['prediction_sha256']
    assert inputs['native']['sha256']==nr['outputs']['physical_branches.json']
    assert all(ap['inputs'][k]['sha256']==inputs[k]['sha256'] for k in ('graph','endpoints','prediction'))
    assert ar['result']['completed']==21140-r['failed']
    alignment=json.loads(paths['alignment'].read_text())
    assert alignment['protocol_sha256']==sha(alignment_root/'protocol.json')
    assert alignment_protocol['inputs_sha256'][p['inputs']['endpoints']['path']]==p['inputs']['endpoints']['sha256']
    assert alignment_protocol['inputs_sha256'][np['inputs']['evaluator_route']['path']]==np['inputs']['evaluator_route']['sha256']
    assert alignment['retained_endpoint_multiset_exact'] and alignment['retained_net_names_match']
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    out.mkdir();(out/'source').mkdir()
    for name in ('evaluate_conv_layer_bbox3.py','prediction_metrics.py','stream_metric_domain.py','pre_route_endpoints.py'):
        shutil.copyfile(Path('tools')/name,out/'source'/name)
    protocol={'inputs':inputs,'source_sha256':{v.name:sha(v) for v in (out/'source').iterdir()},
              'physical_audit_receipt_sha256':sha(physical/'receipt.json'),'native_audit_receipt_sha256':sha(native/'receipt.json'),'alignment_protocol_sha256':sha(alignment_root/'protocol.json'),
              'metrics':'existing resource top5percent and spatial top20; Spearman/MAE/overflow; original string-ID tie order and boundaries disclosed',
              'revision_provenance':p['revision_provenance'],
              'scope':'single corrected frontend baseline; evaluator-only native labels; no feedback or native QoR/net-time claim'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    start=time.monotonic();pred=json.loads(paths['prediction'].read_text());truth=json.loads(paths['native'].read_text())
    endpoints=json.loads(Path(inputs['endpoints']['path']).read_text())
    assert len(pred['connections'])==len(endpoints['connections'])==21140
    fields=('connection_id','net_id','source','sink')
    assert Counter(tuple(v[k] for k in fields) for v in pred['connections'])==Counter(tuple(v[k] for k in fields) for v in endpoints['connections'])
    retained={v['net_id'] for v in endpoints['connections']}
    assert Counter((v['net_id'],v['source'],v['sink']) for v in truth['connections'] if v['net_id'] in retained)==Counter((v['net_id'],v['source'],v['sink']) for v in endpoints['connections'])
    assert nr['retained_endpoint_multiset_exact']
    # Restrict truth occupancy to the identical cohort; refuse additional routed nets.
    assert all(v['net_id'] in retained for v in truth['connections'])
    assert truth['routed_nets']==len(retained)==12867
    assert truth['all_printed_branch_arc_switch_and_union_checks_pass']
    pv=pred['node_occupancy'];tv=truth['node_occupancy']
    rp,rt,sp,st,caps,counts=metric_domain(inputs['graph']['path'],pv,tv)
    reports={'resource':compare(rp,rt,max(1,len(rp)//20)),'spatial':compare(sp,st,20),
             'requested_connections':21140,'completed_connections':ar['result']['completed'],
             'failed_connections':r['failed'],
             'prediction_overflow_units':sum(max(0,v-caps[n]) for n,v in pv.items()),
             'native_overflow_units':sum(max(0,v-caps[n]) for n,v in tv.items())}
    (out/'spatial_maps.json').write_text(json.dumps({'prediction':sp,'native':st})+'\n')
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    assert all(sha(Path('tools')/n)==h for n,h in protocol['source_sha256'].items())
    receipt={'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'node_type_counts':counts,
             'evaluation_s':time.monotonic()-start,'inputs_unchanged':True,'exact_full_cohort_match':True,
             'spatial_maps_sha256':sha(out/'spatial_maps.json'),'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

if __name__=='__main__':run()
