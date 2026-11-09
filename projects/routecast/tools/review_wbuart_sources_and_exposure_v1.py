"""Terminal source evidence and bounded exposure-hint review; no label promotion."""
import datetime,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];N=R/'experiments/wbuart_native_sources_v1_2026-10-20';L=R/'experiments/wbuart_source_lineage_v1_2026-10-20';O=R/'experiments/wbuart_sources_exposure_review_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(Path(__file__))};term=json.loads((N/'terminal.json').read_text());assert len(term['rows'])==3;rows=[]
 for row in term['rows']:
  vp=Path(row['verification']);v=json.loads(vp.read_text());assert row['wrapper_exit_status']==0 and v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and v['exit_status']==0
  for n,h in v['bindings'].items():assert sha(Path(n))==h
  ca=v['canonical'];assert ca['semantic_consistency_gate_pass'] and ca['all_NET_physical_node_type_switch_sequences_identical'] and ca['canonical_original_XML_arc_branch_capacity_pass'] and ca['packed_netlist_byte_identical']
  for n,h in ca['files'].items():assert sha(Path(n))==h
  phys=json.loads((vp.parent/'physical_audit.json').read_text());assert phys['overflow_units']==0 and len(phys['connections'])==2493
  rows.append({k:v[k] for k in ['case','status','iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','complete_case_component_seconds']});bindings[str(vp)]=sha(vp)
 data=json.loads((L/'verification.json').read_text());assert data['scanned_files']==121125 and data['strict_unseen_families_certified']==0;prior=[x for x in data['hits'] if not x['introduced']];assert len(prior)==8 and len({x['sha256'] for x in prior})==1;hints=[];repo=R.parents[1]
 for row in prior:
  p=repo/row['path'];assert sha(p)==row['sha256'];text=p.read_text();assert not row['module_name_overlap'] and row['exact_rtl'] is None and row['aliases']==['zipcpu'];mentions=[{'line':i,'text':s.strip()} for i,s in enumerate(text.splitlines(),1) if 'zipcpu' in s.lower()];assert mentions and all(x['text'].startswith('//') and 'zipcpu.com/dsp/2017/07/22/rounding.html' in x['text'] for x in mentions);hints.append({'path':row['path'],'sha256':row['sha256'],'observed_mentions':mentions,'classification':'comment-only rounding-article reference; not an exact RTL or module-name hit, ancestry still not certified independent'});bindings[str(p)]=sha(p)
 for p in [N/'terminal.json',N/'manifest.json',L/'protocol.json',L/'verification.json',R/'experiments/wbuart_width_frames_v2_2026-10-20/independent_verification_v1.json']:bindings[str(p)]=sha(p)
 report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ALL3_SOURCE_ROUTES_HASH_REVALIDATED_AND8_BOUNDED_EXPOSURE_HINTS_REVIEWED','source_rows':rows,'full_source_endpoint_capacity_and_canonical_gates':True,'source_conditioning_only':True,'new_target_route_labels':False,'exposure_scan_terminal':True,'RTL_files_scanned':data['scanned_files'],'RTL_bytes_scanned':data['scanned_bytes'],'exposure_hints':hints,'exposure_gaps':{'above_2MiB_bound':sum(x['reason']=='above_2MiB_bound' for x in data['gaps']),'FileNotFoundError':sum(x['reason']=='FileNotFoundError' for x in data['gaps'])},'strict_unseen_families_certified':0,'limitations':['Bounded live-workspace source scan is not complete historical/modified-lineage/archives/outside-workspace exposure evidence.','No strict unseen or target quality/route utility/paid-time/hardware success inferred from successful source conditioning.','Original cohort, labels, metric gates and six unavailable ChaCha cases remain unchanged.'],'next_action':'Prepare source conditioning checkpoint and all12 current graph/timing/RC-floor/budget inputs, then freeze complete prospective prediction/ablation/native-utility configuration before any target route labels.','bindings':bindings}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('SOURCE_EXPOSURE_REVIEW_PASS',len(rows),len(prior),flush=True)
if __name__=='__main__':main()
