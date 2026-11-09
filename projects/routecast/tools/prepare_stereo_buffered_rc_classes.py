"""Prepare separate exact electrical context; preserve frozen search CSR."""
import json,time,sys,shutil
from pathlib import Path
from buffered_rc_node_classes import read
from pre_route_endpoints import sha

def run():
    base=Path('experiments/stereo_prospective_validation_2026-10-05')
    out=base/'exact_buffered_rc_classes_v2';out.mkdir();(out/'source').mkdir()
    p=json.loads((base/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host/protocol.json').read_text())
    inputs=p['inputs']['graph'];assert sha(inputs['path'])==inputs['sha256']
    names=('prepare_stereo_buffered_rc_classes.py','buffered_rc_node_classes.py','path_rc.py','pre_route_endpoints.py')
    sources={n:sha(Path('tools')/n) for n in names}
    for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
    protocol={'graph':inputs,'sources':sources,'csr_manifest_sha256':p['csr_manifest_sha256'],
              'scope':'exact node/switch electrical context only; original CSR separate; no search, repair or hardware claim'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
    indices,classes,switches,digest=read(inputs['path'])
    assert digest==inputs['sha256'] and len(indices)==3593250 and len(switches)==4
    if sys.byteorder!='little':indices.byteswap()
    with (out/'node_rc_class_ids.bin').open('wb') as f:indices.tofile(f)
    fraction=lambda v:[v.numerator,v.denominator]
    data={'schema':'ROUTECAST_EXACT_BUFFERED_RC_CLASSES_V1','byteorder':'little','node_count':3593250,
          'node_rc_classes':[[fraction(r),fraction(c)] for r,c in classes],
          'switches':{str(k):[fraction(r),fraction(t)] for k,(r,t) in switches.items()},
          'graph_sha256':digest,'node_class_ids_sha256':sha(out/'node_rc_class_ids.bin')}
    (out/'electrical_context.json').write_text(json.dumps(data)+'\n')
    assert all(sha(Path('tools')/n)==h for n,h in sources.items())
    receipt={'nodes':3593250,'rc_classes':len(classes),'switches':4,'wall_s':time.monotonic()-start,
             'protocol_sha256':sha(out/'protocol.json'),'outputs':{n:sha(out/n) for n in ('node_rc_class_ids.bin','electrical_context.json')},'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

if __name__=='__main__':run()
