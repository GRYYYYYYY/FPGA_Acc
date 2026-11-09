"""Canonical replay only after raw joint admission; no publication."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from loaded_native_canonical_reload import canonical_reload
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux32_limit_retry_native_2026-10-07';rp=base/'receipt.json';vp=base/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['receipt_sha256']==sha(rp) and v['joint_nonregression'];assert all(sha(f)==h for f,h in r['files'].items())
out=ROOT/'experiments/mux32_limit_retry_canonical_2026-10-07';out.mkdir(exist_ok=False);protocol=dict(sources=closure([Path(__file__)]),inputs={str(p):sha(p) for p in (rp,vp)},scope='At most two canonical own-packing zero-fixup FULL/STA replays after raw joint admission; retry uses synchronized own packing and retains first logs; exact original physical paths must be separately verified. No publication or netgain claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();work=out/'input';work.mkdir()
for src,name in [(base/'design.blif','design.blif'),(base/'design.net.post_routing','design.net.post_routing'),(base/'design.place','accepted.place'),(base/'design.route','output.route')]:shutil.copyfile(src,work/name)
cmd=r['command'].copy();cmd[cmd.index('--analysis')]='--route';p=dict(width=32,decision='A',command=cmd,cpd_ns=float(r['cpd_ns']),files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
first_zero_fixup=True
try:result=canonical_reload(p,work,out/'canonical')
except AssertionError:
 first_zero_fixup=False;shutil.copyfile(out/'canonical/design.net.post_routing',work/'design.net.post_routing');p['files']={str(f):sha(f) for f in work.iterdir() if f.is_file()};result=canonical_reload(p,work,out/'canonical_retry')
assert all(sha(f)==h for f,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),parent_native_receipt_sha256=sha(rp),reload=result,first_replay_zero_fixup=first_zero_fixup,seconds=time.perf_counter()-start,scope=protocol['scope']),indent=2)+'\n');print(result['cpd_ns'],result['mismatches'],result['fixups'])
