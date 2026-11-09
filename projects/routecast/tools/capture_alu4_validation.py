"""Freeze a new design capture before native execution; shared inputs read only."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/alu4_validation_capture_2026-10-05');work=Path('work/alu4_validation_capture_2026-10-05')
assert not out.exists() and not work.exists()
base=json.loads(Path('experiments/frisc_graph_capture_2026-10-05/protocol.json').read_text())['inputs']
paths={k:Path(base[k]['path']) for k in ('vpr','arch')};paths['blif']=Path(base['blif']['path']).with_name('alu4.blif')
# Archive the complete current budget/RC/score implementations BEFORE seeing results.
sources=['budget_pin_candidates.py','prepared_budget_pin_candidates.py','buffered_delay_cost.py','local_channel_scores.py','path_rc.py','tree_rc.py','pre_route_endpoints.py']
out.mkdir();work.mkdir();(out/'source').mkdir()
for name in sources:shutil.copyfile(Path('tools')/name,out/'source'/name)
shutil.copyfile(__file__,out/'source'/Path(__file__).name)
shutil.copyfile(paths['blif'],work/'alu4.blif')
cmd=[str(paths['vpr']),str(paths['arch']),'alu4.blif','--route_chan_width','200','--num_workers','1','--seed','1','--max_router_iterations','50','--write_rr_graph','rr_graph.xml','--timing_report_npaths','100','--timing_report_detail','detailed']
protocol={'inputs':{k:{'path':str(p.resolve()),'sha256':sha(p)} for k,p in paths.items()},'command':cmd,'cwd':str(work.resolve()),'timeout_s':300,'scope':'New design not previously named in RouteCast experiments/plan; same architecture, not independently established family holdout. Native routing artifacts reserved for evaluator, not predictor cost tuning.','frozen_sources':{p.name:sha(p) for p in (out/'source').glob('*.py')},'selection':'alu4 chosen from local BLIF availability before execution; no result-based selection','policy':'Retain existing fixed physical pin/original additive RC budget/unique-net capacity/tree/atomic gates; ascending CID; fanout>=64 cohort; label cap100000; no native outcome retuning'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
try:
 with (out/'stdout.log').open('w') as log:r=subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=300)
 code=r.returncode;status='terminal'
except subprocess.TimeoutExpired:code=None;status='timeout'
receipt={'protocol_sha256':sha(out/'protocol.json'),'exit_status':code,'status':status,'wall_s':time.monotonic()-start,'input_identities_unchanged':all(sha(p)==protocol['inputs'][k]['sha256'] for k,p in paths.items()),'artifacts':{p.name:{'path':str(p.resolve()),'sha256':sha(p)} for p in work.iterdir() if p.is_file()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='artifacts'}),flush=True)
assert code==0 and receipt['input_identities_unchanged']
