"""Independent original XML RC/physical audits for every retained family case."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_recurrence_native_reference_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and p['source_sha256']==sha(root/'tools/trial_gf2_recurrence_native_reference.py');assert [row['width'] for row in r['rows']]==[32,64,128];rows=[]
for row in r['rows']:
 assert all(sha(f)==h for f,h in row['files_sha256'].items())
 if not row['native_success']:rows.append({'width':row['width'],'native_failure_retained':True});continue
 directory=out/f"gf2_d{row['width']}";directory.mkdir();protocol={'cwd':row['cwd'],'command':row['command'],'binary_sha256':p['capture_binary_sha256'],'architecture_sha256':p['architecture_sha256']};(directory/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');receipt={**row,'protocol_sha256':sha(directory/'protocol.json')};(directory/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 source=(root/'tools/verify_nonzero_rc_tseng_reference128.py').read_text().replace('experiments/nonzero_rc_tseng_reference128_2026-10-06',str(directory.relative_to(root))).replace("root=Path(__file__).resolve().parents[1]",'root=Path('+repr(str(root))+')').replace('tseng','gf2_frozen_family').replace('Standard benchmark','Frozen generated family').replace('New standard','Frozen generated')
 audit=directory/'audit.py';audit.write_text('import sys\nsys.path.insert(0,'+repr(str(root/'tools'))+')\n'+source)
 log=directory/'audit.log'
 with log.open('w') as stream:code=subprocess.run(['python3',str(audit)],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0;v=json.loads((directory/'verification.json').read_text());assert v['receipt_sha256']==sha(directory/'receipt.json');rows.append({'width':row['width'],'sink_delays_checked':sum(x['sink_delays_checked'] for x in v['results']),'max_absolute_error_s':max(x['max_absolute_error_s'] for x in v['results']),'verification_sha256':sha(directory/'verification.json'),'audit_source_sha256':sha(audit),'audit_log_sha256':sha(log)});print(row['width'],'native paths/delays audited',rows[-1]['sink_delays_checked'],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'rows':rows,'scope':'Full retained frozen family native reference cohort, originalXML branch arcs/unioncapacity/RC versus native SINK FLOAT audited. No predictor transfer, quality advantage, independent upstream family identity or performance proof yet.'},indent=2)+'\n')
