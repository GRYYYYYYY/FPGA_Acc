#!/usr/bin/env python3
"""One placement-seeded SA reanneal plus route/analysis. Outer supervisor times all work."""
import sys,json,subprocess,shutil,time
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'source'))
from tileplace_vpr import validate_contract,sha256
from run_vpr_closure import match
from run_tileplace_v2 import acceptance_reason
p=json.loads((D/'PILOT_PROTOCOL.json').read_text());c=p['cases'][0]['command_template'];arg=lambda f:c[c.index(f)+1]
w=Path(sys.argv[1]); w.mkdir(exist_ok=True)
contract=Path(arg('--contract'));m=json.loads((contract/'manifest.json').read_text());before={f:sha256(Path(arg(f))) for f in ['--input-place','--netlist','--vpr','--architecture','--circuit']}
shutil.copyfile(arg('--netlist'),w/'input.net')
cmd=[arg('--vpr'),arg('--architecture'),arg('--circuit'),'--net_file',str(w/'input.net'),'--read_initial_place_file',arg('--input-place'),'--place_file',str(w/'output.place'),'--route_file',str(w/'output.route'),'--seed','1','--num_workers','1','--route_chan_width','200','--place_algorithm','criticality_timing','--timing_analysis','on','--echo_file','on']
if 'vpr_constraints' in m['inputs']:cmd+=['--read_vpr_constraints',m['inputs']['vpr_constraints']['path']]
cmd+=['--place','--route','--analysis'];(w/'native_command.json').write_text(json.dumps(cmd,indent=2)+'\n')
start=time.monotonic()
with (w/'native.stdout.log').open('w') as out,(w/'native.stderr.log').open('w') as err:r=subprocess.run(cmd,cwd=w,stdout=out,stderr=err)
native=time.monotonic()-start
text=(w/'native.stdout.log').read_text()+(w/'native.stderr.log').read_text()
markers=['Completed placement consistency check successfully.','Completed routing consistency check successfully.','Circuit successfully routed with a channel width factor','VPR succeeded']
checks={x:x in text for x in markers};legal=r.returncode==0 and all(checks.values())
report={'status':'pass' if legal else 'fail','legal':legal,'returncode':r.returncode,'command':cmd,'native_wall_s':native,'markers':checks,'semantics':'placement-seeded reanneal, fresh SA state; no route/temperature/RNG checkpoint continuation','inputs':{f:{'path':arg(f),'sha256':v} for f,v in before.items()}}
if legal:
 report['placement_validation']=validate_contract(contract,w/'output.place')
 report['cpd_ns']=match(r'Final critical path delay \(least slack\):\s+([0-9.]+) ns',text,'CPD',float);report['wirelength']=match(r'Total wirelength:\s+(\d+)',text,'WL',int)
 baseline=json.loads(Path(arg('--baseline-closure')).read_text());report['accepted_against_common_start'],report['acceptance_reason']=acceptance_reason(report,baseline,baseline)
report['outputs']={f:{'path':str(w/f),'bytes':(w/f).stat().st_size,'sha256':sha256(w/f)} for f in ['output.place','output.route','native.stdout.log','native.stderr.log','report_timing.setup.rpt'] if (w/f).exists()}
assert all(sha256(Path(arg(f)))==v for f,v in before.items())
(w/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report));sys.exit(0 if legal else 2)
