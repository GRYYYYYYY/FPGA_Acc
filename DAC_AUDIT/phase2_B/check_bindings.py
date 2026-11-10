"""Verify only frozen sources/direct input identities already recorded in receipts; no corpus scan."""
from pathlib import Path
import json,hashlib,subprocess,sys
D=Path(__file__).resolve().parent;A=D.parent/'phase2_A';P=json.loads((D/'PROTOCOL.json').read_text());R=Path(P['output_root']);S=json.loads((R/'summary.json').read_text());old=json.loads((A/'PILOT_PROTOCOL.json').read_text());expected={x['path']:x['sha256'] for x in old['files']};checked=[]
sys.path.insert(0,str(A/'source'))
from run_v4_timing_protocol import signature,feedback_signature
for row in S['rows']:
 f=R/row['id']/'report.json'
 if row.get('status')!='completed' or row['mode'] not in ['correctness','performance']:continue
 rep=json.loads(f.read_text());assert rep['provenance']['source_and_input_hashes_unchanged_at_completion']
 assert rep['provenance']['implementation']['sha256']==old['implementation']['sha256']
 for v in rep['provenance']['inputs']:assert expected.get(v['path'])==v['sha256'],v['path']
 historic=json.loads((A/'evidence/pilot'/f"{row['case']}_warmup_0_A/exact_signature.json").read_text())
 assert signature(rep)==historic['decisions'] and feedback_signature(rep)==historic['feedback']
 assert rep['phases']==historic['phases'] and [t['transactions'] for t in rep['trials']]==historic['costs']
 checked.append(row['id'])
manifest=json.loads((D/'source_manifest.json').read_text())
for f in manifest['files']:
 b=(D/f['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256'];assert b==subprocess.check_output(['git','show',S['pre_run_commit']+':DAC_AUDIT/phase2_B/'+f['path']],cwd=D)
for f in old['implementation']['sources']:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
receipt={'status':'pass','completed_runs_with_frozen_input_and_reference_identity':checked,'effective_wrapper_files_unchanged_from_pre_run_commit':True,'reference_source_unchanged':True,'all_completed_runs_match_frozen_phase2A_native_trajectory':True,'limits':'Uses frozen direct-input identities and completed-run unchanged checks; no broad raw-file rehash.'}
(D/'evidence/binding_validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
