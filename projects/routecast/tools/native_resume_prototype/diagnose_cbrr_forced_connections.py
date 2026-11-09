"""Diagnose actual selected identities and working-iteration bounds, without target-label policy tuning."""
import json,re,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'experiments/native_resume_cbrr_force_bounds_2026-10-07'
r=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(f)==h for f,h in protocol['bindings'].items())
rows=[]
for row in r['rows']:
 assert all(sha(f)==h for f,h in row['files'].items())
 e=row['events'];selected=[x for x in e if x[0]=='RC_FORCE_SELECT']
 rows.append(dict(width=row['width'],mode=row['mode'],selected_events=len(selected),selected_by_net=dict(Counter(x[2] for x in selected)),clear_net_events=sum(x[0]=='RC_FORCE_CLEAR_NET' for x in e),clear_connection_events=sum(x[0]=='RC_FORCE_CLEAR_CONNECTION' for x in e)))
w=out/'w16_m1_workflow';route=(w/'output.route').read_text();nid=re.search(r'^Net (\d+) \(y6_9\)',route,re.M).group(1)
reads=[x for x in r['rows'][0]['events'] if x[0]=='RC_CBRR_READ' and x[1]==nid]
assert len(reads)==8 and all(float(x[3])==float(x[4])>0 for x in reads)
assert not any(x[0]=='RC_FORCE_SELECT' and x[2]=='y6_9' for x in r['rows'][0]['events'])
report=w/'report_timing.setup.rpt';assert 'Endpoint  : out:y6_9.outpad[0]' in report.read_text().split('#Path 2')[0]
dictout=dict(rows=rows,y6_9=dict(net_id=int(nid),working_iteration_reads=reads,delay_to_saved_bound_ratios=[float(x[3])/float(x[4]) for x in reads],selected=False),receipt_sha256=sha(out/'receipt.json'),diagnostic_sha256=sha(Path(__file__)),limitations='Working-iteration delay/bound equality is not final restored best-route delay. Net clear can arise in whole-net setup or final cleanup and does not prove successful timing repair. No causal QoR or performance improvement claim.')
(out/'forced_diagnosis.json').write_text(json.dumps(dictout,indent=2)+'\n')
print(json.dumps(rows,indent=2))
