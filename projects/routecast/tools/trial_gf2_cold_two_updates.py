"""Cold-only fixed-placement two-update baseline, same native canonical audits."""
import json,os,shutil,subprocess,time,re
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_cold_two_updates_2026-10-06';out.mkdir();work=root/'work/gf2_cold_two_updates_2026-10-06';work.mkdir();shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';cases=[]
for w,count in ((32,264),(64,491),(128,908)):
 original=root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}';swapped=root/f'experiments/gf2_d{w}_placement_swap_2026-10-06';rounds=[]
 for i,target in enumerate((swapped,original)):
  sandbox=work/f'gf2_d{w}'/str(i);sandbox.mkdir(parents=True);shutil.copytree(root/'tools',sandbox/'tools',ignore=shutil.ignore_patterns('__pycache__'));(sandbox/'build').symlink_to(root/'build',target_is_directory=True);(sandbox/'work').mkdir();(sandbox/'experiments').mkdir();(sandbox/'work/gf2_recurrence_native_reference_2026-10-06').symlink_to(root/'work/gf2_recurrence_native_reference_2026-10-06',target_is_directory=True);(sandbox/'experiments/gf2_recurrence_native_reference_2026-10-06').symlink_to(root/'experiments/gf2_recurrence_native_reference_2026-10-06',target_is_directory=True)
  dest=sandbox/f'experiments/gf2_d{w}_placement_swap_2026-10-06';dest.mkdir()
  for n in ('endpoints.json','mapping.json','swapped.place'):shutil.copyfile(swapped/n,dest/n)
  cold='swapped_place_cold' if i==0 else 'fixed_original_cold';canonical='swapped_reference_canonical_reload' if i==0 else 'fixed_original_reference_canonical_reload';stages=[f'{k}_gf2_d{w}_{s}.py' for s in (cold,canonical) for k in ('trial','verify')]
  for name in stages:
   path=sandbox/'tools'/name;s=path.read_text().replace("root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'",'Path('+repr(str(shared))+')')
   if name.startswith('trial_') and canonical in name:
    # Analysis command from own authenticated cold protocol, no candidate dependency.
    start=s.index("original['command']=json.loads(");end=s.index(";assert sha(parent/'receipt.json')",start)
    s=s[:start]+"original['command']=json.loads((parent/'protocol.json').read_text())['command'].copy();original['command'][original['command'].index('--route')]='--analysis'"+s[end:]
   path.write_text(s)
  rounds.append({'sandbox':str(sandbox),'target':str(target/'endpoints.json'),'canonical':canonical,'cold':cold,'stages':stages,'source_sha256':{n:sha(sandbox/'tools'/n) for n in stages}})
 cases.append({'width':w,'count':count,'original':str(original/'endpoints.json'),'initial_route':str(root/f'work/gf2_d{w}_fixed_original_cold_2026-10-06/design.route'),'rounds':rounds})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'source_sha256':sha(Path(__file__)),'scope':'Same three widths, same fixed swapped/original sequence and original native args, fresh cold+canonical+independent audits+finalFULL reload and ledger import. Same archived initial route; excludes initialroutegeneration/frontend/build/sandboxassembly. Cold imports without candidate nonregression prepare policy; no fabricated candidate selection. One serial observation, not paired statistical speed claim.'},indent=2)+'\n');rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for c in cases:
 begin=time.monotonic();w=c['width'];t=time.monotonic();ctx=PersistentRCContext(c['original']);state=import_native_ledger(ctx,c['initial_route']);setup=time.monotonic()-t;rs=[];error=None
 try:
  for i,rd in enumerate(c['rounds']):
   start=time.monotonic();stages=[]
   for name in rd['stages']:
    t=time.monotonic();log=out/f'gf2_d{w}_round{i}_{name}.log'
    with log.open('w') as f:code=subprocess.run(['python3',str(Path(rd['sandbox'])/'tools'/name)],cwd=rd['sandbox'],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
    stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)});print(w,i,name,code,flush=True)
    if code:raise RuntimeError(name)
   parent=Path(rd['sandbox'])/f"experiments/gf2_d{w}_{rd['canonical']}_2026-10-06";q=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');row=q['results'][0];bundle=Path(row['cwd'])/'reload';selected=Path(rd['sandbox'])/'work/final_selected';selected.mkdir()
   for n in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(bundle/n,selected/n)
   t=time.monotonic()
   with (selected/'reload.log').open('w') as f:code=subprocess.run(row['reload_command'],cwd=selected,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
   log=(selected/'reload.log').read_text();assert code==0 and all(x in log for x in ('RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded'));assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1])==row['cpd_ns']
   for pattern in (r'Found (\d+) mismatches',r'Fixed (\d+) routing traces'):assert int(re.search(pattern,log)[1])==0
   final_s=time.monotonic()-t;t=time.monotonic();ctx.bind_endpoints(rd['target']);ctx.set_history({});ctx.native.set_other({});state=import_native_ledger(ctx,selected/'design.route');advance=time.monotonic()-t;assert len(state.records)==c['count'];file=out/f'gf2_d{w}_accepted{i+1}.json';file.write_text(json.dumps({'revision':i+1,'records':[state.records[k] for k in sorted(state.records)],'ledger':dict(state.ledger),'scale':ctx.rc.scale,'endpoint_metadata':ctx.endpoint_metadata},indent=2)+'\n');rs.append({'round':i,'stages':stages,'final_FULL_s':final_s,'ledger_import_s':advance,'cpd_ns':row['cpd_ns'],'round_wall_s':time.monotonic()-start,'snapshot_sha256':sha(file),'native_receipt_sha256':sha(parent/'receipt.json'),'selected_files_sha256':{str(p):sha(p) for p in selected.iterdir() if p.is_file()}})
 except Exception as ex:error=repr(ex)
 rows.append({'width':w,'context_import_s':setup,'rounds':rs,'case_wall_s':time.monotonic()-begin,'complete':len(rs)==2,'error':error});(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==len(cases)},indent=2)+'\n');print(w,'complete',len(rs)==2,rows[-1]['case_wall_s'],error,flush=True)
