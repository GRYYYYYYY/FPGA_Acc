"""Evaluate corrected full stereo baseline only after physical witness audit."""
import json,time,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import compare
from stream_metric_domain import metric_domain

PREDICTIONS=('ordinary_additive_class_cache_prediction_undriven_v2',
             'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host')

def run(name=PREDICTIONS[0]):
    if name not in PREDICTIONS:raise ValueError('unsupported prediction artifact')
    base=Path('experiments/stereo_prospective_validation_2026-10-05')
    parent=base/name;native=base/'native_route_labels_audit'
    physical=base/(name+'_physical_audit');out=base/('ordinary_additive_undriven_v2_evaluation' if name==PREDICTIONS[0] else 'ordinary_additive_undriven_v2_authenticated_host_evaluation')
    if out.exists():raise ValueError('fresh output required')
    p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text())
    nr=json.loads((native/'receipt.json').read_text());ar=json.loads((physical/'receipt.json').read_text())
    assert p['endpoints_version']=='endpoints_undriven_v2'
    assert r['protocol_sha256']==sha(parent/'protocol.json')
    assert ar['prediction_receipt_sha256']==sha(parent/'receipt.json')
    assert ar['protocol_sha256']==sha(physical/'protocol.json')
    ap=json.loads((physical/'protocol.json').read_text())
    assert ar['result']['all_physical_and_union_checks_passed']
    assert ar['result']['requested']==81610
    assert nr['protocol_sha256']==sha(native/'protocol.json')
    assert nr['physical_checks_pass']
    paths={'prediction':parent/'prediction.json','native':native/'physical_branches.json',
           'alignment':base/'endpoints_undriven_v2/accounting_alignment_audit.json'}
    inputs={k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()}
    inputs.update({k:p['inputs'][k] for k in ('graph','endpoints')})
    assert inputs['prediction']['sha256']==r['prediction_sha256']
    assert inputs['native']['sha256']==nr['outputs']['physical_branches.json']
    assert all(ap['inputs'][k]['sha256']==inputs[k]['sha256'] for k in ('graph','endpoints','prediction'))
    assert ar['result']['completed']==81610-r['failed']
    alignment=json.loads(paths['alignment'].read_text())
    assert alignment['native_retained_multiset_exact'] and alignment['endpoint_sha256']==inputs['endpoints']['sha256']
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    out.mkdir();(out/'source').mkdir()
    for name in ('evaluate_stereo_baseline.py','prediction_metrics.py','stream_metric_domain.py','pre_route_endpoints.py'):
        shutil.copyfile(Path('tools')/name,out/'source'/name)
    protocol={'inputs':inputs,'source_sha256':{v.name:sha(v) for v in (out/'source').iterdir()},
              'physical_audit_receipt_sha256':sha(physical/'receipt.json'),
              'metrics':'existing resource top5percent and spatial top20; Spearman/MAE/overflow; original string-ID tie order and boundaries disclosed',
              'revision_provenance':alignment['revision_provenance'],
              'scope':'single corrected frontend baseline; evaluator-only native labels; no feedback or native QoR/net-time claim'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    start=time.monotonic();pred=json.loads(paths['prediction'].read_text());truth=json.loads(paths['native'].read_text())
    endpoints=json.loads(Path(inputs['endpoints']['path']).read_text())
    assert len(pred['connections'])==len(endpoints['connections'])==81610
    fields=('connection_id','net_id','source','sink')
    assert Counter(tuple(v[k] for k in fields) for v in pred['connections'])==Counter(tuple(v[k] for k in fields) for v in endpoints['connections'])
    retained={v['net_id'] for v in endpoints['connections']}
    assert Counter((v['net_id'],v['source'],v['sink']) for v in truth['connections'] if v['net_id'] in retained)==Counter((v['net_id'],v['source'],v['sink']) for v in endpoints['connections'])
    assert all(v['net_id'] in retained for v in truth['connections'])
    pv=pred['node_occupancy'];tv=truth['node_occupancy']
    rp,rt,sp,st,caps,counts=metric_domain(inputs['graph']['path'],pv,tv)
    reports={'resource':compare(rp,rt,max(1,len(rp)//20)),'spatial':compare(sp,st,20),
             'requested_connections':81610,'completed_connections':ar['result']['completed'],
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

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--prediction',choices=PREDICTIONS,default=PREDICTIONS[0])
    run(parser.parse_args().prediction)
