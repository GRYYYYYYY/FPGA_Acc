import json,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_sequence_views_2026-10-06';work=root/'work/native_candidate_sequence_views_2026-10-06';r=json.loads((out/'receipt.json').read_text());rows={x['sequence']:x for x in r['results']};assert set(rows)=={'A','AR','AA','ARA','ARR','AAAR'}
graph=r['command'][r['command'].index('--read_rr_graph')+1];files=[out/'receipt.json',Path(r['command'][0])];audited=0
for seq,row in rows.items():
 assert row['exit_code']==0 and all(sha(f)==h for f,h in row['inputs_sha256'].items())
 cwd=work/seq;case=out/seq;log=(case/'run.log').read_text();steps=re.findall(r'ROUTECAST sequence step=(\d+) decision=([AR])',log);assert steps==[(str(i),d) for i,d in enumerate(seq)]
 assert log.count('moved candidate passed native FULL routing check')==len(seq)
 assert log.count('candidate uses canonical packing view at step=')==len(seq)
 assert log.count('accepted actual moved candidate after FULL check, packing sync and STA')==seq.count('A')
 assert log.count('restored delay matrix and all edge-delay/STA metric observations')==seq.count('R')
 armed=re.findall(r'armed context-bound candidate sync ticket epoch=(\d+)',log);consumed=re.findall(r'consume context-bound candidate sync ticket epoch=(\d+)',log);expected=list(map(str,range(1,len(armed)+1)));assert armed==consumed==expected
 assert len(armed)==seq.count('A')+(seq[-1]=='R')
 paths=list(cwd.glob('candidate_*.route'));assert len(paths)==len(seq)
 for p in [cwd/'output.route',*paths]:
  a=audit(graph,p);assert len(a['connections'])==129 and a['overflow_units']==0;audited+=1
 assert sha(cwd/'output.route')==row['route_sha256'] and sha(cwd/'design.net.post_routing')==row['packed_sha256']
 assert 'Placement_ID: SHA256:'+sha(cwd/'accepted.place') in (cwd/'output.route').read_text().splitlines()[0]
 assert 'Netlist_ID: SHA256:'+sha(cwd/'design.net') in (cwd/'accepted.place').read_text().splitlines()[0]
 files.extend(p for p in cwd.iterdir() if p.is_file());files.extend(p for p in case.iterdir() if p.is_file())
for a,b in [('A','AR'),('A','ARR'),('AA','ARA'),('A','AAAR')]:
 for key in ('route_sha256','packed_sha256','cpd_ns'):assert rows[a][key]==rows[b][key]
 for f in ('accepted.place','output.route','design.net.post_routing'):assert (work/a/f).read_bytes()==(work/b/f).read_bytes()
original=json.loads((root/'experiments/native_scoped_sync_next_move_2026-10-06/receipt.json').read_text())['results'][-1]
for key in ('route_sha256','packed_sha256','cpd_ns'):assert rows['A'][key]==original[key]
assert rows['A']['route_sha256']!=rows['AA']['route_sha256']
verified={'audited_route_files':audited,'candidate_steps':sum(map(len,rows)),'cases':len(rows),'sha256':{str(p):sha(p) for p in files},'checks':['actual same-process candidate sequences with FULL legality and per-candidate independent physical checks','all scoped ticket epochs armed and consumed exactly once in order','rejected decisions restore most recent accepted route/packed/place byte identity against prefix controls','all input hashes unchanged and placement-to-route digest chain verified'],'scope':'One reconstructed multiplier case, fixed compatible pair, canonical pre-sync view plus accepted post-sync view. Recursive cold candidate harness; no generic performance or exception-safety guarantee.'}
(out/'verification.json').write_text(json.dumps(verified,indent=2)+'\n');print('verified',audited,'routes')
