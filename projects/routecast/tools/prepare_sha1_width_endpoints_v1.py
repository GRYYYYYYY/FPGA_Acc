"""Separate label-free endpoint copies of authenticated per-width RR exports."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha,extract
D=R/'experiments/sha1_width_endpoints_v1_2026-10-10';D.mkdir();src=R/'experiments/sha1_native_width_cohort_v1_2026-10-10';rp=src/'receipt.json';receipt=json.loads(rp.read_text());assert receipt['all_cases_attempted'] and all(sha(k)==v for k,v in receipt['bindings'].items());bindings={str(rp):sha(rp),str(Path(__file__)):sha(Path(__file__))};rows=[]
for original in receipt['rows']:
 width=original['width'];w=D/str(width);w.mkdir()
 for k,v in original['files'].items():assert sha(k)==v
 for f in ['design.blif','design.net','design.place','rr_graph.xml']:shutil.copyfile(src/str(width)/f,w/f);bindings[str(src/str(width)/f)]=sha(src/str(width)/f)
 ep,mapping=extract(w/'design.net',w/'design.place',w/'rr_graph.xml');(w/'endpoints.json').write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n')
 rows.append(dict(name=str(width),status='AUTHENTICATED_WIDTH_EXPORT_ENDPOINTS_CAPTURED',original_native_exit_code=original['exit_code'],connections=len(ep['connections']),files={str(p):sha(p) for p in w.iterdir() if p.is_file()}))
assert all(sha(k)==v for k,v in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
print('CAPTURED',[(r['name'],r['connections']) for r in rows])
