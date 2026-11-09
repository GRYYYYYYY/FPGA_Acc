import json,shutil,subprocess,os,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_packing_rollback_2026-10-06';work=root/'work/native_packing_rollback_2026-10-06';out.mkdir();work.mkdir();meta=json.loads((root/'experiments/predictor_native_trace_import_2026-10-06/command.json').read_text());src=Path(meta['cwd']);cmd=meta['command'];cmd[0]=str(root/'build/native_packing_rollback_v2_2026-10-06/routecast_packing_rollback_vpr')
for f in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(src/f,work/f)
env=os.environ.copy();env['ROUTECAST_PACKING_ROLLBACK_DIR']=str(out)
with (out/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
assert code==0;assert sha(out/'before.txt')==sha(out/'restored.txt');assert sha(out/'mutated.txt')!=sha(out/'before.txt');text=(out/'run.log').read_text();assert 'VPR succeeded' in text and 'restored packing hierarchy' in text;cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]);assert cpd==3.64796
(out/'receipt.json').write_text(json.dumps({'exit_code':code,'before_after_state_sha256':sha(out/'before.txt'),'mutated_state_sha256':sha(out/'mutated.txt'),'cpd_ns':cpd,'log_sha256':sha(out/'run.log'),'binary_sha256':sha(cmd[0]),'command':cmd,'scope':'Same-process post-sync exception restores copied complete pb objects, AtomLookup and clustering maps; then real synchronization/analysis succeeds. Active serialized state equality, not full pb private map serialization or whole move atomicity.'},indent=2)+'\n');print('packing mutated, restored, then resynchronized; CPD',cpd)
