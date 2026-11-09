import json,shutil,subprocess,os,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_import_v2_2026-10-06';out.mkdir();work=root/'work/native_seed_import_v2_2026-10-06';work.mkdir();src=root/'work/native_identity_remapped_reload_2026-10-06'
for name in ('design.blif','design.net','design.place'):shutil.copyfile(src/name,work/name)
shutil.copyfile(src/'design.route',work/'seed.route')
c=json.loads((root/'experiments/native_synchronized_bundle_reload_2026-10-06/rebound_bundle_command.json').read_text())['command'];c[0]=str(root/'build/native_seed_import_v2_2026-10-06/routecast_seed_vpr');c[c.index('--analysis')]='--route';c[c.index('--route_file')+1]='output.route'
env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(work/'seed.route');(out/'command.json').write_text(json.dumps({'command':c,'cwd':str(work),'seed':env['ROUTECAST_NATIVE_SEED']},indent=2)+'\n');start=time.monotonic()
with (out/'run.log').open('w') as f:code=subprocess.run(c,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
(out/'receipt.json').write_text(json.dumps({'exit_code':code,'wall_s':time.monotonic()-start,'scope':'Actual route stage with post-initialization seed import; explicit importer pres_fac=.5 acc_fac=1; not prospective or performance proof.'},indent=2)+'\n');print(code)
