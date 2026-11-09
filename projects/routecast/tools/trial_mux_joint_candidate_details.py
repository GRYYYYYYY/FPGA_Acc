"""Candidate-owned packing + full endpoint detailed timing, all four forecasts."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from loaded_native_canonical_reload import canonical_reload
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_retained_joint_quality_gate_2026-10-06';out=ROOT/'experiments/mux_joint_candidate_details_2026-10-06';out.mkdir();r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');rows=[]
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(base/'receipt.json'),source_sha256=sha(Path(__file__)),scope='All four complete forecasts; aggregate full8*width endpoint timing. First replay may synchronize reference packing; only zero-fixup replay certifies candidate. Preserve raw first evidence.'),indent=2)+'\n')
for row,ver in zip(r['rows'],v['rows']):
 if row['status']!='RELOADED':continue
 w,i=row['width'],row['index'];source=base/f'w{w}_m{i}';work=out/f'w{w}_m{i}';work.mkdir()
 for name in ('design.blif','design.net.post_routing','accepted.place'):shutil.copyfile(source/name,work/name)
 shutil.copyfile(source/'predicted.route',work/'output.route');command=row['native']['command']+['--timing_report_detail','aggregated','--timing_report_npaths',str(w*8)];p=dict(width=w,decision='A',command=command,cpd_ns=float(format(ver['predicted_cpd_ns'],'.6g')),files={str(f):sha(f)for f in work.iterdir()if f.is_file()});first=None
 try:first=canonical_reload(p,work,work/'initial_replay')
 except AssertionError:pass
 if first is None:
  shutil.copyfile(work/'initial_replay/design.net.post_routing',work/'design.net.post_routing');p['files']={str(f):sha(f)for f in work.iterdir()if f.is_file()};result=canonical_reload(p,work,work/'candidate_canonical')
 else:result=first
 rows.append(dict(width=w,index=i,first_replay_zero_fixup=first is not None,reload=result));(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(w,i,result['cpd_ns'],flush=True)
