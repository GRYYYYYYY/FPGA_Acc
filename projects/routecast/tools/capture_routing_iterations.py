"""Run an isolated, frozen VPR route-only development capture."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('vpr','arch','blif','net','place','graph','work_dir','output_dir'):
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--channel-width',type=int,required=True);a=p.parse_args()
    if a.channel_width<1:raise ValueError('invalid channel width')
    if a.work_dir.exists() or a.output_dir.exists():raise ValueError('choose fresh isolated directories')
    a.work_dir.mkdir(parents=True);a.output_dir.mkdir(parents=True)
    inputs={k:{'path':str(getattr(a,k).resolve()),'sha256':sha(getattr(a,k))} for k in ('vpr','arch','blif','net','place','graph')}
    metadata=ET.parse(a.net).getroot().attrib
    if metadata.get('architecture_id')!='SHA256:'+inputs['arch']['sha256']:raise ValueError('architecture identity mismatch')
    if metadata.get('atom_netlist_id')!='SHA256:'+inputs['blif']['sha256']:raise ValueError('atom netlist identity mismatch')
    for name in ('blif','net','place'):shutil.copyfile(getattr(a,name),a.work_dir/f'diffeq.{name}')
    command=[str(a.vpr.resolve()),str(a.arch.resolve()),'diffeq.blif','--route',
             '--net_file','diffeq.net','--place_file','diffeq.place','--route_file','diffeq.route',
             '--read_rr_graph',str(a.graph.resolve()),'--route_chan_width',str(a.channel_width),
             '--save_routing_per_iteration','on','--num_workers','1','--seed','1',
             '--max_router_iterations','50','--timing_report_npaths','1']
    protocol={'schema':'ROUTECAST_NATIVE_ROUTING_CAPTURE_V1','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'inputs':inputs,'command':command,'cwd':str(a.work_dir.resolve()),'source_sha256':sha(Path(__file__)),
              'scope':'one development route-only run, single CPU worker, same packed netlist/placement/RR graph; no sketch feedback',
              'completion_criteria':'exit 0, final .route and one or more iteration_*.route; inspect router status before claims'}
    (a.output_dir/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    started=time.monotonic()
    with (a.output_dir/'vpr_stdout.txt').open('w') as log:
        result=subprocess.run(command,cwd=a.work_dir,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=False)
    iterations=sorted(a.work_dir.glob('iteration_*.route'))
    receipt={'exit_code':result.returncode,'wall_s':time.monotonic()-started,'protocol_sha256':sha(a.output_dir/'protocol.json'),
             'input_identities_unchanged':all(sha(entry['path'])==entry['sha256'] for entry in inputs.values()),
             'iteration_files':[{'path':str(path.resolve()),'sha256':sha(path)} for path in iterations],
             'final_route':{'path':str((a.work_dir/'diffeq.route').resolve()),'sha256':sha(a.work_dir/'diffeq.route')} if (a.work_dir/'diffeq.route').exists() else None,
             'log_sha256':sha(a.output_dir/'vpr_stdout.txt')}
    (a.output_dir/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'exit_code':result.returncode,'iteration_routes':len(iterations),'wall_s':receipt['wall_s']}),flush=True)
    if result.returncode or not iterations or receipt['final_route'] is None:raise SystemExit(1)
