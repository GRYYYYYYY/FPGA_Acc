import json,shutil,subprocess,os
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_move_identities_2026-10-06';out.mkdir();work=root/'work/native_move_identities_2026-10-06';work.mkdir();src=root/'work/multiplier_family_native_capture_2026-10-06/mult_6x6';proto=json.loads((root/'experiments/native_search_seed_v3_2026-10-06/command.json').read_text())['command'];proto[0]=str(root/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr');proto[proto.index('--route')]='--analysis';proto[proto.index('--route_file')+1]='missing.route';results=[]
for case in ('initial','moved'):
 cwd=work/case;cwd.mkdir()
 for f in ('design.blif','design.net'):shutil.copyfile(src/f,cwd/f)
 place=src/'design.place' if case=='initial' else root/'experiments/multiplier_placement_swap_2026-10-06/mult_6x6/swapped.place';shutil.copyfile(place,cwd/'design.place');env=os.environ.copy();env['ROUTECAST_NET_IDENTITY_FILE']=str(out/(case+'.jsonl'))
 with (out/(case+'.log')).open('w') as f:code=subprocess.run(proto,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert (out/(case+'.jsonl')).exists();results.append({'case':case,'exit_code':code,'identity_sha256':sha(out/(case+'.jsonl')),'packed_sha256':sha(cwd/'design.net'),'placement_sha256':sha(cwd/'design.place')})
old={r['name']:r for r in map(json.loads,(out/'initial.jsonl').read_text().splitlines())};new={r['name']:r for r in map(json.loads,(out/'moved.jsonl').read_text().splitlines())};assert set(old)==set(new)
affected=[]
for name in old:
 assert old[name]['net_id']==new[name]['net_id'];a=old[name]['pins'];b=new[name]['pins'];assert len(a)==len(b)
 if a!=b:affected.append({'name':name,'net_id':new[name]['net_id']})
(out/'receipt.json').write_text(json.dumps({'cases':results,'affected_nets':affected,'command':proto,'scope':'Native identity capture before expected missing route rejection, same original packed netlist at actual old/new placements; no route generated.'},indent=2)+'\n');print('affected',len(affected))
