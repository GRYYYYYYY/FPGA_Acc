"""Same-cohort arithmetic evaluation, original resource/spatial metric rules."""
import argparse
import json
import shutil
import time
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from prediction_metrics import compare
from stream_metric_domain import metric_domain


def main():
    parser=argparse.ArgumentParser();parser.add_argument('design');parser.add_argument('model',choices=['sparse_reset','bbox3']);args=parser.parse_args()
    base=Path('experiments');parent=base/'adder_tree_family_predictions_2026-10-06'/args.design/args.model
    native=base/'adder_tree_family_native_path_audit_2026-10-06'/args.design;physical=Path(str(parent)+'_physical_audit')
    p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());nr=json.loads((native/'receipt.json').read_text());ar=json.loads((physical/'receipt.json').read_text())
    assert r['protocol_sha256']==sha(parent/'protocol.json') and r['prediction_sha256']==sha(parent/'prediction.json')
    assert ar['protocol_sha256']==sha(physical/'protocol.json') and ar['prediction_receipt_sha256']==sha(parent/'receipt.json')
    assert ar['result']['all_physical_and_union_checks_passed'] and ar['result']['requested']==r['connections'] and ar['result']['completed']==r['connections']-r['failed']
    assert nr['protocol_sha256']==sha(native/'protocol.json') and nr['physical_checks_pass'] and nr['retained_endpoint_multiset_exact']
    np=json.loads((native/'protocol.json').read_text());assert np['inputs']['rr_graph']==p['inputs']['graph'] and np['inputs']['endpoints']==p['inputs']['endpoints'] and np['frontend_receipt_sha256']==p['frontend_receipt_sha256']
    assert all(sha(v['path'])==v['sha256'] for v in np['inputs'].values())
    assert all(sha(native/'source'/name)==h for name,h in np['source_sha256'].items())
    assert all(sha(native/name)==h for name,h in nr['outputs'].items())
    pred=json.loads((parent/'prediction.json').read_text());truth=json.loads((native/'physical_branches.json').read_text());ep=json.loads(Path(p['inputs']['endpoints']['path']).read_text())
    fields=('connection_id','net_id','source','sink');assert Counter(tuple(v[k] for k in fields) for v in pred['connections'])==Counter(tuple(v[k] for k in fields) for v in ep['connections'])
    expected=Counter((v['net_id'],v['source'],v['sink']) for v in ep['connections']);actual=Counter((v['net_id'],v['source'],v['sink']) for v in truth['connections']);assert expected==actual,'refuse extra native cohort'
    assert truth['routed_nets']==len({v['net_id'] for v in ep['connections']})
    out=base/'adder_tree_family_evaluation_2026-10-06'/args.design/args.model;out.mkdir(parents=True);(out/'source').mkdir()
    names=['evaluate_adder_tree_predictions.py','prediction_metrics.py','stream_metric_domain.py','pre_route_endpoints.py']
    for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
    inputs={**p['inputs'],'prediction':{'path':str((parent/'prediction.json').resolve()),'sha256':r['prediction_sha256']},'native':{'path':str((native/'physical_branches.json').resolve()),'sha256':nr['outputs']['physical_branches.json']}}
    protocol={'inputs':inputs,'source_sha256':{n:sha(out/'source'/n) for n in names},'physical_audit_receipt_sha256':sha(physical/'receipt.json'),'native_audit_receipt_sha256':sha(native/'receipt.json'),
              'metrics':'unchanged resource top5percent, spatial top20; original string-ID tie rules','unseen_family_claim':False,'scope':'arithmetic readiness cohort, evaluator-only native reference; not native feedback QoR or total time gain'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
    pv=pred['node_occupancy'];tv=truth['node_occupancy'];rp,rt,sp,st,caps,counts=metric_domain(inputs['graph']['path'],pv,tv)
    reports={'resource':compare(rp,rt,max(1,len(rp)//20)),'spatial':compare(sp,st,20),'requested_connections':r['connections'],'completed_connections':ar['result']['completed'],'failed_connections':r['failed'],'prediction_overflow_units':sum(max(0,v-caps[n]) for n,v in pv.items()),'native_overflow_units':sum(max(0,v-caps[n]) for n,v in tv.items())}
    (out/'spatial_maps.json').write_text(json.dumps({'prediction':sp,'native':st})+'\n')
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values()) and all(sha(Path('tools')/n)==h for n,h in protocol['source_sha256'].items())
    result={'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'node_type_counts':counts,'evaluation_s':time.monotonic()-start,'exact_full_cohort_match':True,'spatial_maps_sha256':sha(out/'spatial_maps.json'),'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
