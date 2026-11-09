"""Verify every native endpoint/units binding and conservative binary32 floor value."""
import json,struct,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_singlepass_floor_controls_2026-10-07';quality=json.loads((out/'verification.json').read_text());assert all(sha(f)==h for f,h in quality['bindings'].items())
f32=lambda x:struct.unpack('<f',struct.pack('<f',float(x)))[0]
def down(x):
 x=f32(x)
 if x==0:return 0.0
 bits=struct.unpack('<I',struct.pack('<f',x))[0];return struct.unpack('<f',struct.pack('<I',bits-1))[0]
rows=[]
for w,i in ((16,1),(32,3)):
 for mode in ('workflow','cold'):
  base=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_{mode}_2026-10-07';file=base/'rr_floors.txt';lines=file.read_text().splitlines();tag,digest,nodes,count=lines[0].split();assert tag=='ROUTECAST_FLOORS_SECONDS_V1';floors={}
  for line in lines[1:]:s,t,value=line.split();key=int(s),int(t);assert key not in floors;floors[key]=float(value)
  assert len(floors)==int(count)
  meta=json.loads((ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json').read_text());assert digest==meta['graph_sha256'];target=Counter((q['source'],q['sink']) for q in meta['connections']);assert set(floors)==set(target)
  ctx=json.loads((base/'floor_context/epoch_1/receipt.json').read_text());assert ctx['graph_sha256']==digest;exact={}
  for answer in ctx['answers']:
   q=answer['query'];key=q['source'],q['sink'];value=F(answer['minimum_integer'],ctx['scale']);assert floors[key]==float(value);exact[key]=value
  events=[line.split() for line in (base/'first/run.log').read_text().splitlines() if line.startswith('RC_FLOOR_BIND ')];assert len(events)==len(meta['connections']);observed=Counter();lowered=0
  for e in events:
   key=int(e[4]),int(e[5]);observed[key]+=1;current=f32(e[6]);actual=f32(e[7]);expected=min(current,down(floors[key]));assert actual==expected
   assert F(actual)<=exact[key] or actual==current<down(floors[key]);lowered+=actual<current
  assert observed==target
  loaded=[line.split() for line in (base/'first/run.log').read_text().splitlines() if line.startswith('RC_FLOORS_LOADED ')];assert loaded==[['RC_FLOORS_LOADED',str(len(floors)),digest]]
  stage=json.loads((base/'receipt.json').read_text())['stages'][0];assert stage['stage']=='independent_target_rr_floor_preparation'
  rows.append(dict(width=w,index=i,mode=mode,bound_connections=len(events),lowered_bounds=lowered,bridge_binary32_exact=True,rr_floor_preparation_seconds=stage['seconds'],triggered_whole_nets=sum(line.startswith('RC_FORCE_WHOLE_NET ') for line in (base/'first/run.log').read_text().splitlines())))
# Evaluate new candidate against old unfloored cold as an explicit reference, not a label for online policy.
old=json.loads((ROOT/'experiments/native_resume_ungated_controls_2026-10-07/verification.json').read_text());assert all(sha(f)==h for f,h in old['bindings'].items());comparisons=[]
for q in quality['rows']:
 previous=next(x for x in old['rows'] if x['width']==q['width']);comparisons.append(dict(width=q['width'],new_candidate_cpd=q['cpd_pair'][0],unfloored_cold_cpd=previous['cpd_pair'][1],new_candidate_wire=q['wire_pair'][0],unfloored_cold_wire=previous['wire_pair'][1],joint_vs_unfloored_cold=F(q['cpd_pair'][0])<=F(previous['cpd_pair'][1]) and q['wire_pair'][0]<=previous['wire_pair'][1],new_matched_cold_wire=q['wire_pair'][1]))
result=dict(quality_verification_sha256=sha(out/'verification.json'),old_control_sha256=sha(ROOT/'experiments/native_resume_ungated_controls_2026-10-07/verification.json'),verifier_sha256=sha(Path(__file__)),rows=rows,reference_comparisons=comparisons,scope='Every SOURCE/SINK and seconds/binary32 floor binding verified, graph digest validated by launcher; native loader checks node count/coverage, does not independently cryptographically validate graph digest. Initial min(achieved, relaxed floor), later native lower-bound updates still enabled. Fresh estimator construction paid separately in all four full pipelines, no sequence amortization or heldout/time gain claim.')
(out/'bridge_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(rows);print(comparisons)
