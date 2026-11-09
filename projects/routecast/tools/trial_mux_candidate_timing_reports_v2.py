"""Original-VPR canonical candidate analysis; preserve rejected replays."""
import json,re,shutil
from pathlib import Path
from pre_route_endpoints import sha
from loaded_native_canonical_reload import canonical_reload
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_budget_repair_quality_gate_2026-10-06';out=ROOT/'experiments/mux_candidate_timing_reports_v2_2026-10-06';out.mkdir()
r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(base/'receipt.json'),source_sha256=sha(Path(__file__)),scope='All three original candidate replays. Candidate packing taken from archived original-VPR synchronization; reject nonzero fixups or CPD discrepancy. Initial synchronization is provenance, not zero-fixup evidence. No accepted bundle mutation.'),indent=2)+'\n')
rows=[]
for row,ver in zip(r['rows'],v['rows']):
 w=row['width'];source=base/f'w{w}';work=out/f'w{w}';work.mkdir()
 for name in ('design.blif','design.net.post_routing','accepted.place'):shutil.copyfile(source/name,work/name)
 shutil.copyfile(ROOT/f'experiments/mux_candidate_timing_reports_2026-10-06/w{w}/canonical/design.net.post_routing',work/'design.net.post_routing')
 shutil.copyfile(source/'predicted.route',work/'output.route')
 p=dict(width=w,decision='A',command=row['native']['command'],cpd_ns=float(format(ver['predicted_cpd_ns'],'.6g')),files={str(f):sha(f)for f in work.iterdir() if f.is_file()})
 try:
  result=canonical_reload(p,work,work/'canonical');entry=dict(width=w,status='ZERO_FIXUP_RELOADED',reload=result)
 except Exception as e:entry=dict(width=w,status='REJECTED',error=repr(e))
 rows.append(entry);(out/'receipt.json').write_text(json.dumps(dict(rows=rows,protocol_sha256=sha(out/'protocol.json')),indent=2)+'\n');print(w,entry['status'],flush=True)
