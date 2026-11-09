"""Join quality/cost controls and actual native wholeNET trigger events."""
import json,re,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_wholenet_controls_2026-10-07';bindings={};versions={}
for policy in ('tol101','wholenet'):
 f=ROOT/f'experiments/native_resume_{policy}_controls_2026-10-07/verification.json';d=json.loads(f.read_text());assert all(sha(p)==h for p,h in d['bindings'].items());bindings[str(f)]=sha(f);versions[policy]=d
rows=[]
for w,i in ((16,1),(32,3)):
 for mode in ('workflow','cold'):
  base=ROOT/f'experiments/native_resume_wholenet_w{w}_m{i}_{mode}_2026-10-07';log=base/'first/run.log';report=base/'canonical/report_timing.setup.rpt'
  for f in (log,report):bindings[str(f)]=sha(f)
  events=[line.split() for line in log.read_text().splitlines() if line.startswith('RC_FORCE_WHOLE_NET')]
  body=report.read_text().split('#Path 2')[0]
  rows.append(dict(width=w,index=i,mode=mode,whole_net_events=events,trigger_count=len(events),triggered_nets=dict(Counter(x[3] for x in events)),worst_startpoint=re.search(r'^Startpoint: (.+)$',body,re.M)[1],worst_endpoint=re.search(r'^Endpoint  : (.+)$',body,re.M)[1]))
paths={}
for mode in ('workflow','cold'):
 f=ROOT/f'experiments/native_resume_wholenet_w16_m1_{mode}_2026-10-07/first/output.route';bindings[str(f)]=sha(f);paths[mode]=physical_paths(f)
branch=lambda mode:[p for p in paths[mode]['s6_0'] if p[-1][0]==4018]
assert len(branch('workflow'))==len(branch('cold'))==1
result=dict(bindings=bindings,source_sha256=sha(Path(__file__)),rows=rows,s6_0_sink4018_path_equals_policy_matched_cold=branch('workflow')==branch('cold'),quality_passes=versions['wholenet']['quality_passes'],aggregate_ratio=versions['wholenet']['aggregate_ratio'],scope='State-triggered wholeNET is only new policy factor vs tol101; policy applied to both modes. One serial timing pair per case; no stable gain and both cases fail joint quality. WholeNET intervention may affect other routes, not isolated single-prefix causality.')
(out/'ablation_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print([(x['width'],x['mode'],x['trigger_count']) for x in rows]);print('Diagnosed s6 branch equals new cold:',result['s6_0_sink4018_path_equals_policy_matched_cold'])
