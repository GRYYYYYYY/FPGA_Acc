import json,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1]
out=root/'experiments/native_scoped_sync_next_move_2026-10-06';work=root/'work/native_scoped_sync_next_move_2026-10-06'
r=json.loads((out/'receipt.json').read_text());assert all(x['exit_code']==0 for x in r['results'])
baseline=json.loads((root/'experiments/native_accepted_next_move_2026-10-06/receipt.json').read_text())
for current,old in zip(r['results'],baseline['results']):
 for key in ('case','route_sha256','packed_sha256','cpd_ns'):assert current[key]==old[key]
log=(out/'accept_next/run.log').read_text();assert log.count('armed context-bound candidate sync ticket epoch=1')==1 and log.count('consume context-bound candidate sync ticket epoch=1')==1
a,b,c=r['results'];assert a['route_sha256']==b['route_sha256'] and a['packed_sha256']==b['packed_sha256'];assert a['cpd_ns']==b['cpd_ns'];assert c['route_sha256']!=a['route_sha256']
cmd=json.loads((out/'accept_next/command.json').read_text())['command'];graph=cmd[cmd.index('--read_rr_graph')+1]
for name in ('reject_next','accept_next'):
 p=work/name/'candidate.route';v=audit(graph,p);assert len(v['connections'])==129 and v['overflow_units']==0
 (out/name/'candidate_physical_audit.json').write_text(json.dumps(v,indent=2)+'\n')
 log=(out/name/'run.log').read_text();assert 'moved candidate passed native FULL routing check' in log
 if name=='reject_next':assert 'restored delay matrix and all edge-delay/STA metric observations' in log
place=work/'accept_next/accepted.place';route=work/'accept_next/output.route'
assert 'Placement_ID: SHA256:'+sha(place) in route.read_text().splitlines()[0]
assert 'Netlist_ID: SHA256:'+sha(work/'accept_next/design.net') in place.read_text().splitlines()[0]
files=[out/'receipt.json',Path(cmd[0])]
for name in ('resume','reject_next','accept_next'):
 command=json.loads((out/name/'command.json').read_text());assert all(sha(p)==h for p,h in command['inputs_sha256'].items())
 files.extend((out/name).glob('*'));files.extend((work/name).glob('*'))
verified={'sha256':{str(p):sha(p) for p in files if p.is_file()},'checks':['all three fresh-process runs exit zero','rejected move restores route and packed bytes and CPD','both real candidates pass native FULL and independent 129-connection zero-overflow audit','accepted placement digest matches final route; placement bound to input packed netlist'],'scope':'Fixed block pair, fresh-process continuation from reconstructed accepted bundle; not continuous in-memory transactions or general performance evidence.'}
(out/'verification.json').write_text(json.dumps(verified,indent=2)+'\n');print('verified')
