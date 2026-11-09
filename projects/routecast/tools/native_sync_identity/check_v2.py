"""Native same-process pre/post sync identity capture with exact output parity."""
import json,sys,shutil,subprocess,os,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_sync_identity_parity_v2_2026-10-07';o.mkdir(exist_ok=False);binary=R/'build/native_sync_identity_v2_2026-10-07/routecast_sync_identity_vpr';rows=[];bindings={str(binary):sha(binary),str(Path(__file__)):sha(Path(__file__))}
for i in (1,3):
 b=R/f'experiments/native_resume_shared_cold_adder_step{i}_workflow_2026-10-07';r=json.loads((b/'receipt.json').read_text());src=b/'exchange_native';w=o/f'step{i}';w.mkdir()
 for f in ('design.blif','design.net','design.place','design.route'):bindings[str(src/f)]=sha(src/f);shutil.copyfile(src/f,w/f)
 cmd=list(r['canonical']['command']);cmd[0]=str(binary);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_SYNC_IDENTITY_PREFIX']=str(w/'sync')
 with (w/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 body=(w/'run.log').read_text();assert code==0 and 'VPR succeeded' in body
 for f in ('design.net.post_routing','design.route','report_timing.setup.rpt'):assert (w/f).read_bytes()==(src/f).read_bytes(),f
 assert (w/'sync.before.jsonl').read_bytes()==(b/'canonical/identity.jsonl').read_bytes()
 before={x['name']:x for x in map(json.loads,(w/'sync.before.jsonl').read_text().splitlines())};after={x['name']:x for x in map(json.loads,(w/'sync.after.jsonl').read_text().splitlines())};fresh={x['name']:x for x in map(json.loads,(b/'exchange_canonical/identity.jsonl').read_text().splitlines())};assert before.keys()==after.keys()==fresh.keys()
 rows.append(dict(index=i,exit_code=code,cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',body)[-1],exact_native_route_post_NET_setup_report=True,before_table_exact_input_native_identity=True,before_after_changed_net_records=sum(before[n]!=after[n] for n in before),live_after_vs_fresh_persisted_changed_net_records=sum(after[n]!=fresh[n] for n in after),files={str(f):sha(f) for f in w.iterdir() if f.is_file()}));print(rows[-1]['index'],rows[-1]['before_after_changed_net_records'],rows[-1]['live_after_vs_fresh_persisted_changed_net_records'],flush=True)
assert all(sha(p)==h for p,h in bindings.items());(o/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Private original-native sync wrapper captures live identity before/after real sync; exact output parity. No candidate commit, transaction rollback, normalization-free final proof or speed claim. Live clb NET IDs differ from separately reloaded post-routing packed NET identity.'),indent=2)+'\n')
