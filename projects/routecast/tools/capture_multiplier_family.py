"""Fixed arithmetic cohort capture, isolated one-worker native runs."""
import json
import shutil
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha


def main():
    root=Path(__file__).resolve().parents[1]
    front=root/'experiments/multiplier_family_frontend_2026-10-06'
    fr=json.loads((front/'receipt.json').read_text())
    assert sha(front/'protocol.json')==fr['protocol_sha256']
    vtr=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    vpr=vtr/'build_tileplace_vpr/vpr/vpr'
    arch=vtr/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml'
    out=root/'experiments/multiplier_family_native_capture_2026-10-06';out.mkdir()
    work=root/'work/multiplier_family_native_capture_2026-10-06';work.mkdir(parents=True)
    shutil.copy2(vpr,out/'vpr');assert sha(vpr)==sha(out/'vpr')
    snapshot=out/'sources';snapshot.mkdir()
    sources=['pre_route_endpoints.py','nonclock_global_pins.py','prepare_length_switch_csr.py','prepared_csr.py','streaming_csr_converter.py','replay_adder_tree_prediction.py','affected_search_context.py',
             'conv_layer_length_switch_sparse_reset_prediction.py','conv_layer_length_switch_bbox3_prediction.py',
             'csr_consumer/authenticated_host_sparse_reset_search.hpp','csr_consumer/authenticated_host_bounded_search.hpp']
    frozen={}
    for name in sources:
        p=root/'tools'/name
        if not p.exists():
            # Record absence rather than pretend a wrong source was frozen.
            frozen[name]={'present':False};continue
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        frozen[name]={'present':True,'sha256':sha(p)}
    for binary_name in ('routecast_csr_authenticated_sparse_reset','routecast_csr_authenticated_bounded'):
        p=root/'build'/binary_name;shutil.copy2(p,snapshot/binary_name);frozen['build/'+binary_name]={'present':True,'sha256':sha(p)}
    shutil.copyfile(__file__,out/'source.py')
    protocol={'frontend_receipt_sha256':sha(front/'receipt.json'),'vpr_original_sha256':sha(vpr),
              'architecture':{'path':str(arch),'sha256':sha(arch)},'source_sha256':sha(__file__),
              'frozen_predictor_sources':frozen,'models':'length-switch unrestricted sparse reset and fixed bbox3; no parameter tuning on native results',
              'cohort':[r['design'] for r in fr['results']],'seed':1,'route_chan_width':300,'num_workers':1,
              'timeout_per_design_s':120,'unseen_family_claim':False,
              'scope':'all six fixed multiplier readiness cases; packed/place/RR graph and evaluator-only native reference; no end-to-end benefit claim'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    results=[]
    for r in fr['results']:
        name=r['design'];design=front/name/'design.blif'
        assert sha(design)==r['artifacts']['design.blif']
        wd=work/name;wd.mkdir();shutil.copyfile(design,wd/'design.blif')
        command=[str(out/'vpr'),str(arch),'design.blif','--route_chan_width','300','--num_workers','1','--seed','1','--max_router_iterations','100','--write_rr_graph','rr_graph.xml']
        (out/(name+'_command.json')).write_text(json.dumps({'command':command,'cwd':str(wd),'input_sha256':sha(design)},indent=2)+'\n')
        print(json.dumps({'stage':'native_started','design':name}),flush=True)
        start=time.monotonic()
        with (out/(name+'.log')).open('w') as log:
            try:
                code=subprocess.run(command,cwd=wd,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode;timeout=False
            except subprocess.TimeoutExpired:code=None;timeout=True
        result={'design':name,'exit_code':code,'timed_out':timeout,'wall_s':time.monotonic()-start,
                'artifacts':{p.name:{'path':str(p),'sha256':sha(p)} for p in wd.iterdir() if p.is_file()},
                'input_unchanged':sha(design)==r['artifacts']['design.blif']}
        (out/(name+'_receipt.json')).write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(json.dumps({k:result[k] for k in ('design','exit_code','timed_out','wall_s')}),flush=True)
    assert sha(arch)==protocol['architecture']['sha256'] and sha(vpr)==protocol['vpr_original_sha256']
    (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results,
        'all_exit_zero':all(r['exit_code']==0 for r in results),'scope':protocol['scope']},indent=2)+'\n')


if __name__=='__main__':main()
