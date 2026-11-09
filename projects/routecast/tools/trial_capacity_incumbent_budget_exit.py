"""One-iteration repair-budget exhaustion with legal seed fallback."""
import json,os,re,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/capacity_incumbent_budget_exit_2026-10-06';out.mkdir();work=root/'work/capacity_incumbent_budget_exit_2026-10-06';work.mkdir();parent=root/'experiments/capacity_seed_incumbent_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==v['receipt_sha256'];source_row=next(x for x in r['results'] if x['pair_index']==8 and x['max_criticality']=='0' and not x['guard']);source=Path(source_row['cwd']);assert all(sha(p)==h for p,h in source_row['files_sha256'].items());env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};results=[]
for guard in (False,True):
 cwd=work/str(int(guard));cwd.mkdir()
 for n in ('design.net','design.place','design.blif','seed.route','repair_names.txt'):shutil.copyfile(source/n,cwd/n)
 cmd=source_row['command']+['--max_router_iterations','1'];runenv={**env,'ROUTECAST_NATIVE_SEED':str(cwd/'seed.route'),'ROUTECAST_REPAIR_NET_NAMES':str(cwd/'repair_names.txt')}
 if guard:runenv['ROUTECAST_SEED_INCUMBENT']='1'
 with (cwd/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=runenv,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(cwd/'run.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);physical=None
 if code==0:
  graph=cmd[cmd.index('--read_rr_graph')+1];physical=audit(graph,cwd/'output.route');assert len(physical['connections'])==516 and physical['overflow_units']==0
 results.append({'guard':guard,'exit_code':code,'native_success':'VPR succeeded' in log,'cpd_ns':float(cpd[1]) if cpd else None,'connections':len(physical['connections']) if physical else None,'cwd':str(cwd),'command':cmd,'files_sha256':{str(p):sha(p) for p in cwd.iterdir() if p.is_file()}});print(guard,code,results[-1]['cpd_ns'],flush=True)
assert results[0]['exit_code']!=0 and results[1]['exit_code']==0 and results[1]['cpd_ns']==source_row['seed_cpd_ns'];(out/'receipt.json').write_text(json.dumps({'results':results,'source_sha256':sha(Path(__file__)),'parent_verification_sha256':sha(parent/'verification.json'),'scope':'Actual one-iteration repair-budget exhaustion: no legal new repair expected, guard restores input legal seed. Not injected exception/OOM recovery or production transaction.'},indent=2)+'\n')
