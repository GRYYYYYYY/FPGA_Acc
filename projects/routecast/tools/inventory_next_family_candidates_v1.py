"""Bounded filename evidence and prospective selection, without target labels."""
import datetime, hashlib, json, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
OUT=R/'experiments/next_family_candidate_inventory_v1_2026-10-20'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):
 with (OUT/name).open('x') as f: json.dump(obj,f,indent=2); f.write('\n')
def main():
 OUT.mkdir(exist_ok=False)
 old=R/'experiments/prospective_external_family_nonJSON_exposure_v1_2026-10-18/verification.json'
 historical=list(json.loads(old.read_text())['snapshot'])
 candidates=[{'candidate':'wbuart32','aliases':['wbuart','zipcpu_uart'],'proposed_repository':'https://github.com/ZipCPU/wbuart32'}, {'candidate':'sdspi','aliases':['sdspi','zipcpu_sd'],'proposed_repository':'https://github.com/ZipCPU/sdspi'}, {'candidate':'verilog-i2c','aliases':['verilog-i2c','verilog_i2c','i2c_master'],'proposed_repository':'https://github.com/alexforencich/verilog-i2c'}]
 protocol={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection_order':[c['candidate'] for c in candidates], 'criteria':['Non-cryptographic RTL family to broaden development coverage beyond ChaCha.', 'Explicit license and pinned official commit/tree/blob provenance required before RTL use.', 'Hierarchy closure checked before technology synthesis; no target routing labels used for selection.', 'First candidate in frozen order with reproducible frontend closure proceeds; failures retained, never ranked by congestion quality.'], 'current_scope':'Filename hints only; repository addresses are proposed identifiers, not verified availability.', 'strict_unseen_certified':False,'historical_snapshot_sha256':sha(old),'candidates':candidates,'preserved':'Existing cohort, labels, gates, all negative findings and six unavailable width cases unchanged.'}
 write('protocol.json',protocol)
 cmd=['rg','--files','--hidden','--no-ignore','-g','!**/.git/**','-g','!**/node_modules/**','-g','!projects/tileplace/work/full_color_trial_volatile_address_stage_2026-10-04/**','projects']
 result=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True,check=True)
 names=result.stdout.splitlines()
 rows=[]
 for c in candidates:
  match=lambda n:any(a in n.lower() for a in c['aliases'])
  rows.append({'candidate':c['candidate'],'historical_filename_hits':[n for n in historical if match(n)],'current_filename_hits':[n for n in names if match(n)],'qualification':'candidate_only_history_and_archive_payload_ancestry_unresolved'})
 evidence=[]
 for suffix in ['temporal_prior_utilization','budget_reuse_factorial','budget_astar_factorial']:
  p=R/f'experiments/prospective_external_family_{suffix}_v1_2026-10-19/research_decision_v1.json'
  d=json.loads(p.read_text()); evidence.append({'path':str(p.relative_to(R)),'sha256':sha(p),'status':d.get('status'),'decision':d.get('decision')})
 write('verification.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'BOUNDED_FILENAME_INVENTORY_AND_SELECTION_ORDER_FROZEN','historical_filename_count':len(historical),'current_filename_count':len(names),'enumeration_command':cmd,'filename_stream_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'rows':rows,'negative_score_evidence':evidence,'strict_unseen_families_certified':0,'target_label_files_read':False,'rtl_acquired':False,'limitations':['No metadata content search in this inventory.','No archive payload inspection or outside-workspace history attestation.','No absence-to-unseen inference.'],'bindings':{'protocol.json':sha(OUT/'protocol.json'),'tool':sha(Path(__file__))}})
 print(json.dumps({'status':'inventory complete','filename_count':len(names),'rows':[{k:v if not isinstance(v,list) else len(v) for k,v in row.items()} for row in rows]}))
if __name__=='__main__': main()
