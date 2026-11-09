"""Every failed simple obligation assigned to exact archived netname/port, no waiver."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];p=R/'experiments/supported_equivalence_progress_v2_2026-10-10/verification.json';v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());row=next(x for x in v['rows'] if x['name']=='stereovision0');assert row['complete_logged_simple_attempt_count']==21619 and row['simple_failed_count']==2287;jp=R/'experiments/verilog_frontend_cohort_v3_2026-10-10/stereovision0/design.json';m=json.loads(jp.read_text())['modules']['stereovision0'];failed=[];groups=Counter();ports=Counter();unresolved=[]
for x in row['all_logged_simple_attempts']:
 if x['simple_proved']:continue
 match=re.fullmatch(r'\\(.+?)(?: \[(\d+)\])?',x['point']);assert match,x['point'];name=match[1];index=int(match[2]) if match[2] is not None else None;desc=m['netnames'].get(name);record=dict(point=x['point'],netname=name,index=index,archived_netname_present=desc is not None)
 if desc is not None:
  offset=desc.get('offset',0);width=len(desc['bits']);j=0 if index is None else index-offset
  if desc.get('upto',0):j=width-1-j
  if 0<=j<width:record['archived_bit']=desc['bits'][j]
  else:record['index_not_in_archived_range']=True
 else:unresolved.append(x['point'])
 port=m['ports'].get(name);record['top_port_direction']=None if port is None else port['direction'];ports[record['top_port_direction'] or 'internal']+=1;groups[name]+=1;failed.append(record)
assert len(failed)==2287
D=R/'experiments/stereovision0_unproved_point_diagnosis_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,jp]};(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,all2287_failed_simple_points=failed,groups=dict(groups),port_categories=dict(ports),unresolved_names=unresolved,scope='All original logged simple failures, exact archived netname/range lookup and top-port classification. Failed obligation means unproved, not mismatch; no proof-point deletion or output-only replacement, source/native/family admission false.'),indent=2)+'\n');print(json.dumps(dict(failed=len(failed),groups=len(groups),port_categories=dict(ports),unresolved_names=len(unresolved),largest_groups=groups.most_common(8))))
