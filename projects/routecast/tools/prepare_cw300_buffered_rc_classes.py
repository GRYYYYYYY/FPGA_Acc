"""Prepare separate exact electrical context; preserve frozen search CSR."""
import json,time,sys,shutil,argparse
from pathlib import Path
from buffered_rc_node_classes import read
from pre_route_endpoints import sha

def run():
    parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();base=Path('experiments')
    out=base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/args.design;out.mkdir(parents=True);(out/'source').mkdir()
    p=json.loads((base/'multiplier_family_predictions_2026-10-06'/args.design/'sparse_reset/protocol.json').read_text());prepared=json.loads((base/'multiplier_family_length_switch_csr_2026-10-06'/args.design/'receipt.json').read_text())
    inputs=p['inputs']['graph'];assert sha(inputs['path'])==inputs['sha256']
    names=('prepare_cw300_buffered_rc_classes.py','buffered_rc_node_classes.py','path_rc.py','pre_route_endpoints.py')
    sources={n:sha(Path('tools')/n) for n in names}
    for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
    protocol={'graph':inputs,'sources':sources,'csr_manifest_sha256':p['csr_manifest_sha256'],
              'scope':'exact node/switch electrical context only; original CSR separate; no search, repair or hardware claim'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
    indices,classes,switches,digest=read(inputs['path'])
    assert digest==inputs['sha256'] and len(indices)==prepared['nodes'] and len(switches)>0
    if sys.byteorder!='little':indices.byteswap()
    with (out/'node_rc_class_ids.bin').open('wb') as f:indices.tofile(f)
    fraction=lambda v:[v.numerator,v.denominator]
    data={'schema':'ROUTECAST_EXACT_BUFFERED_RC_CLASSES_V1','byteorder':'little','node_count':len(indices),
          'node_rc_classes':[[fraction(r),fraction(c)] for r,c in classes],
          'switches':{str(k):[fraction(r),fraction(t)] for k,(r,t) in switches.items()},
          'graph_sha256':digest,'node_class_ids_sha256':sha(out/'node_rc_class_ids.bin')}
    (out/'electrical_context.json').write_text(json.dumps(data)+'\n')
    assert all(sha(Path('tools')/n)==h for n,h in sources.items())
    receipt={'nodes':len(indices),'rc_classes':len(classes),'switches':len(switches),'wall_s':time.monotonic()-start,
             'protocol_sha256':sha(out/'protocol.json'),'outputs':{n:sha(out/n) for n in ('node_rc_class_ids.bin','electrical_context.json')},'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

if __name__=='__main__':run()
