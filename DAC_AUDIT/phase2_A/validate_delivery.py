#!/usr/bin/env python3
"""Independent compact delivery checks; never launches an experiment."""
from pathlib import Path
import csv,json,hashlib,subprocess,sys,time
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'source'))
from tileplace_vpr import parse_place
start=time.monotonic()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open()))
p=json.loads((D/'PILOT_PROTOCOL.json').read_text());receipt=json.loads((D/'PRE_RUN_COMMIT.json').read_text());R=Path(p['output_root']);summary=json.loads((R/'summary.json').read_text());out={}
assert sha(D/'PILOT_PROTOCOL.json')==receipt['protocol_sha256']
assert subprocess.check_output(['git','show',receipt['pre_run_commit']+':DAC_AUDIT/phase2_A/PILOT_PROTOCOL.json'],cwd=D)==(D/'PILOT_PROTOCOL.json').read_bytes()
out['protocol_precedes_runs']=receipt
out['source_files']=[]
for f in sorted((D/'source').glob('*.py')):
 b=subprocess.check_output(['git','show',receipt['pre_run_commit']+':DAC_AUDIT/phase2_A/source/'+f.name],cwd=D);assert b==f.read_bytes();out['source_files'].append({'file':f.name,'sha256':sha(f),'matches_pre_run_commit':True})
for name in ['run_pilot.py','baseline_smoke.py','test_pressure_switch.py']:
 assert subprocess.check_output(['git','show',receipt['pre_run_commit']+':DAC_AUDIT/phase2_A/'+name],cwd=D)==(D/name).read_bytes()
h=rows(D/'all_cases.csv');tr=rows(D/'evidence/historical_trial_index.csv');assert len(h)==13 and sum(r['status']=='pass' for r in h)==9 and sum(r['status']=='fail' for r in h)==4 and len(tr)==404
out['history']={'cases':13,'successes':9,'failures':4,'native_trials':404}
roots={};parts={}
for r in rows(D/'timing_breakdown.csv'):
 if r['stage']=='outer_total':roots[r['run_id']]=float(r['wall_s'])
 if r.get('exclusive_partition')=='True':parts[r['run_id']]=parts.get(r['run_id'],0)+float(r['wall_s'])
assert roots and all(abs(parts[k]-v)<1e-5 for k,v in roots.items());out['timing_partitions_verified']=len(roots)
checks=[]
expected_inputs={r['path']:r['sha256'] for r in p['files']}
for row in summary['runs']:
 if row.get('status')!='completed' or row['arm']=='B1':continue
 w=R/row['run_id'];r=json.loads((w/'report.json').read_text());assert r['provenance']['implementation']['sha256']==p['implementation']['sha256'];assert sha(w/'final.place')==r['output_place']['sha256']
 for v in r['provenance']['inputs']:assert expected_inputs.get(v['path'])==v['sha256'],(row['run_id'],v['path'])
 assert json.loads((w/'timing.json').read_text())['pressure_prefix']==(row['arm']=='A')
 if 'report_path' in r['final']:
  n=json.loads(Path(r['final']['report_path']).read_text());_,a=parse_place(w/'final.place');_,b=parse_place(Path(n['outputs']['vpr_place_copy']['path']));assert a and a==b;assert sha(w/'final.place')==n['inputs']['golden_place']['sha256'];assert n['legal'];checks.append({'run_id':row['run_id'],'placement_rows_compared':len(a),'native_input_sha_matches_final':True,'all_placement_fields_equal':True})
 else:checks.append({'run_id':row['run_id'],'final_source':'original_baseline_no_new_accepted_trial'})
 assert len(r['trials'])>0
 for t in r['trials']:
  assert sha(Path(t['candidate_place']['path']))==t['candidate_place']['sha256'];assert sha(Path(t['closure']['report_path']))==t['closure']['report_sha256']
out['native_output_binding']=checks
out['normalization']='VPR may rewrite Netlist_File, comment divider and tab padding; all parsed placement fields and exact native input SHA are checked.'
# The first warmup is only a reference: cross-arm comparisons must be nonempty.
comparisons=[]
for case in p['cases']:
 rr=[r for r in summary['runs'] if r['case']==case['case'] and r['kind']!='baseline_smoke' and r.get('status')=='completed'];aa=[r for r in rr if r['arm']=='A'];bb=[r for r in rr if r['arm']=='B']
 if aa and bb:
  ref=json.loads((R/aa[0]['run_id']/'exact_signature.json').read_text());assert ref['decisions']['trials']
  comparisons.append({'case':case['case'],'cross_arm_comparisons':len(bb),'all_equal':all(json.loads((R/b['run_id']/'exact_signature.json').read_text())==ref for b in bb)})
 else:comparisons.append({'case':case['case'],'cross_arm_comparisons':0,'all_equal':'NOT_ESTABLISHED'})
out['cross_arm_checks']=comparisons
for f in (D/'evidence').rglob('*'):
 if f.is_file():assert f.stat().st_size<8*1024**2
size=sum(f.stat().st_size for f in D.rglob('*') if f.is_file() and '__pycache__' not in f.parts);assert size<50*1024**2;out['package_bytes_before_validation_receipt']=size
out['offline_delivery_verification_s']=time.monotonic()-start
out['status']='pass' if all(x['all_equal'] is True for x in comparisons) else 'incomplete_or_mismatch_retained'
(D/'evidence/delivery_validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['source_files','native_output_binding']},indent=2))
