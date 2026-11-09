"""Original full-source six-step output reset contract, separate from full temporal proof."""
import ast,json,sys,subprocess,os
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];ip=R/'experiments/supported_initial_state_interfaces_v1_2026-10-10/audit.json';inventory=json.loads(ip.read_text());assert all(sha(k)==h for k,h in inventory['bindings'].items());base=R/'tools/check_blob_merge_reset_alignment_sat_v1.py';body=base.read_text();D=R/'experiments/supported_reset_alignment_cohort_v1_2026-10-10';assert not D.exists();D.mkdir();cases=[];bindings={str(x):sha(x) for x in [Path(__file__).resolve(),ip,base]}
for name in ['diffeq1','diffeq2','stereovision1','stereovision2']:
 row=next(x for x in inventory['rows'] if x['name']==name);assert len(row['reset_named_input_candidates'])==1;reset=row['reset_named_input_candidates'][0];clocks=row['all_clock_reset_control_counts'];assert len(clocks)==1 and clocks[0]['pin']=='C' and len(clocks[0]['bits'])==1;assert any(p['direction']=='input' and p['bits']==clocks[0]['bits'] for p in row['all_top_ports'].values())
 src='experiments/verilog_frontend_cohort_v3_2026-10-10/'+name;out=str((D/name).relative_to(R));changes=[("R=Path(__file__).resolve().parents[1]",f'R=Path({str(R)!r})'),('experiments/blob_merge_frontend_readiness_v1_2026-10-10',src),('experiments/blob_merge_reset_alignment_sat_v1_2026-10-10',out),('RLE_BlobMerging',row['top']),('in_iReset','in_'+reset)];code=body
 for a,b in changes:code=code.replace(a,b)
 normalized=code
 for a,b in changes:normalized=normalized.replace(b,a)
 assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(body));adapter=D/(name+'.py');adapter.write_text(code);bindings[str(adapter)]=sha(adapter);cases.append(dict(name=name,adapter=str(adapter),reset=reset,top=row['top']))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='Four complete original one-direct-clock JSON designs, all outputs compared; six steps active-high reset first2/low last4, symbolic otherinputs/independent arbitraryinitial states,120s each. Contract test not an assumption of source reset sufficiency/polarity; failures interpreted against actual source. No unbounded or source-family/native admission. Original induction obligations retained separately.'),indent=2)+'\n');rows=[]
for case in cases:
 with (D/(case['name']+'.log')).open('w') as log:code=subprocess.run([sys.executable,case['adapter']],cwd=R,env={**os.environ,'PYTHONPATH':str(R/'tools')},stdout=log,stderr=subprocess.STDOUT).returncode
 p=D/case['name']/'receipt.json';row=dict(name=case['name'],wrapper_exit=code,receipt=str(p),receipt_present=p.exists())
 if p.exists():
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p);row.update(exit_code=v['exit_code'],reset_alignment_sat_success=v['reset_alignment_sat_success'])
 rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all4_attempted=len(rows)==4,scope='Bounded startup contract only; no full temporal/native/family admission.'),indent=2)+'\n')
