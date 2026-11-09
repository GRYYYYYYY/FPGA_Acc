"""Archive original XML witness verification after revised conv_layer baseline search."""
import json,time,shutil
from pathlib import Path
from streaming_prediction_audit import verify
from pre_route_endpoints import sha

def run():
    prediction_root=Path('experiments/conv_layer_length_switch_prediction_v2_2026-10-06');out=Path(str(prediction_root)+'_physical_audit')
    if out.exists():raise ValueError('fresh output required')
    p=json.loads((prediction_root/'protocol.json').read_text());r=json.loads((prediction_root/'receipt.json').read_text())
    expected_connections=21140
    assert r['protocol_sha256']==sha(prediction_root/'protocol.json') and r['prediction_sha256']==sha(prediction_root/'prediction.json') and r['journal_sha256']==sha(prediction_root/'net_results.jsonl')
    assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
    inputs={**p['inputs'],'prediction':{'path':str((prediction_root/'prediction.json').resolve()),'sha256':r['prediction_sha256']}}
    modules=['streaming_prediction_audit.py','physical_prediction_audit.py','prepared_csr.py','pre_route_endpoints.py','net_union_topology.py']
    source={name:sha(Path('tools')/name) for name in modules}
    out.mkdir();(out/'source').mkdir()
    for name in modules:shutil.copyfile(Path('tools')/name,out/'source'/name)
    shutil.copyfile(__file__,out/'driver.py')
    protocol={'inputs':inputs,'source_sha256':source,'prediction_receipt_sha256':sha(prediction_root/'receipt.json'),'expected_connections':expected_connections,'endpoints_version':p.get('endpoints_version','endpoints'),'frontend_revision_scope':p.get('frontend_revision_scope','original frontend'),'scope':'independent original XML witness, cohort, counters, net-union occupancy and uncalibrated congestion scores; no route tree/pin or native legality'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    start=time.monotonic();e=json.loads(Path(inputs['endpoints']['path']).read_text());prediction=json.loads(Path(inputs['prediction']['path']).read_text())
    assert len(e['connections'])==expected_connections
    result=verify(inputs['graph']['path'],e,prediction,topology=True)
    assert result['requested']==expected_connections
    assert result['completed']==expected_connections-r['failed']
    assert result['all_physical_and_union_checks_passed']
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values()) and all(sha(Path('tools')/n)==h for n,h in source.items())
    receipt={'result':result,'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'prediction_receipt_sha256':protocol['prediction_receipt_sha256'],'inputs_unchanged':True,'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'requested':result['requested'],'completed':result['completed'],'all_type_overuse_units':result['all_type_overuse_units'],'wall_s':receipt['wall_s'],'receipt_sha256':sha(out/'receipt.json')}),flush=True)
if __name__=='__main__':run()
