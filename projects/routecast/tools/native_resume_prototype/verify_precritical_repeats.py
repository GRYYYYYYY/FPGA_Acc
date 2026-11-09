"""Authenticate every repeated pair and report every cost/QoR outcome."""
import json,statistics,sys
from fractions import Fraction as F
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_precritical_repeats_2026-10-07'
pp,tp=base/'protocol.json',base/'timers.json';p,t=json.loads(pp.read_text()),json.loads(tp.read_text());assert t['protocol_sha256']==sha(pp)
assert len(t['rows'])==8 and [(r['pair'],r['mode']) for r in t['rows']]==[tuple(x) for x in p['order']]
assert sha(Path(__file__).with_name('precritical_repeat_trial.py'))==p['producer_sha256']
reference=ROOT/'experiments/native_resume_critical_release_v7_2026-10-07/resume/canonical/design.route'
norm=lambda f:{name:Counter(ps) for name,ps in physical_paths(f).items() if ps}
ref=norm(reference);bindings={str(f):sha(f) for f in (pp,tp,reference,Path(__file__))};runs={}
for timer in t['rows']:
 tag,mode=timer['pair'],timer['mode'];assert timer['exit_code']==0
 log=base/f'{tag}_{mode}.log';assert sha(log)==timer['log_sha256'];bindings[str(log)]=sha(log)
 root=ROOT/f'experiments/native_resume_precritical_repeat_{tag}_{mode}_2026-10-07'
 rp,sp=root/'receipt.json',root/'protocol.json';r,s=json.loads(rp.read_text()),json.loads(sp.read_text());assert r['protocol_sha256']==sha(sp)
 for mapping in (r['files'],s['inputs'],s['sources'],r['canonical']['files']):
  for file,digest in mapping.items():assert sha(file)==digest;bindings[file]=digest
 assert r['canonical']['mismatches']==r['canonical']['fixups']==0 and r['all_target_endpoints_match'] and r['raw_canonical_paths_preserved'] and r['physical_audit']['overflow_units']==0
 assert len(r['physical_audit']['connections'])==1929
 assert sum(st['seconds'] for st in r['stages'])<=r['internal_seconds']<=timer['external_seconds']
 assert sum('native' in st for st in r['stages'])==1
 if mode=='workflow':assert r['feedback']['net']=='y3_7' and r['feedback']['eligible'] and norm(root/'canonical/design.route')==ref
 bindings.update({str(rp):sha(rp),str(sp):sha(sp)});runs[tag,mode]=(r,s,timer)
rows=[]
for tag in ('p0','p1','p2','p3'):
 w,ws,wt=runs[tag,'workflow'];c,cs,ct=runs[tag,'cold']
 shared=set(ws['inputs'])&set(cs['inputs']);assert all(ws['inputs'][file]==cs['inputs'][file] for file in shared)
 for suffix in ('target_endpoints.json','target.place','design.net','design.blif','rr_graph.xml'):assert any(file.endswith(suffix) for file in shared)
 joint=F(w['cpd_ns'])<=F(c['cpd_ns']) and w['wirelength']<=c['wirelength']
 rows.append(dict(pair=tag,workflow_seconds=wt['external_seconds'],cold_seconds=ct['external_seconds'],ratio=wt['external_seconds']/ct['external_seconds'],joint_nonregression=joint,cpd_pair=[w['cpd_ns'],c['cpd_ns']],wire_pair=[w['wirelength'],c['wirelength']],net_time_gain=wt['external_seconds']<ct['external_seconds']))
assert all(sha(file)==digest for file,digest in bindings.items())
result=dict(bindings=bindings,rows=rows,quality_passes=sum(r['joint_nonregression'] for r in rows),time_wins=sum(r['net_time_gain'] for r in rows),median_paired_ratio=statistics.median(r['ratio'] for r in rows),aggregate_ratio=sum(r['workflow_seconds'] for r in rows)/sum(r['cold_seconds'] for r in rows),scope=p['scope']+'; fixed development single move, allinitialmapping/seed/endpoint/RRproduction excluded, no heldout or raw-input end-to-end; descriptive observations, no significance/stable speedup claim')
(base/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(rows);print(result['time_wins'],result['median_paired_ratio'],result['aggregate_ratio'])
