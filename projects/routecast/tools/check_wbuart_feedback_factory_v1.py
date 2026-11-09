"""All12 baseline bit parity, all21 physical path snapshots, identity rejection."""
import csv,hashlib,json
from pathlib import Path
from wbuart_fixed_nominal_feedback_factory_v1 import create
R=Path(__file__).resolve().parents[1];E=R/'experiments';M=E/'wbuart_feedback_factory_v1_2026-10-20/manifest.json';O=E/'wbuart_feedback_factory_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 O.mkdir(exist_ok=False);manifest=read(M);rows=[];snapshots=0;connections=0;negative=0;bindings={str(p):sha(p) for p in [Path(__file__),M]}
 for r in manifest['rows']:
  ep=Path(r['endpoint']);model,b=create(ep);bindings.update(b);base=Path(r['baseline']);initial=read(Path(r['initial']));rr={(int(q['net']),int(q['pin'])):float(q['delay_s']) for q in csv.DictReader((base/'initial_connections.tsv').open(),delimiter='\t')};values=model.analyze_rr(rr);fields=['criticality_bits','raw_criticality_bits','slack_bits','criticality_numerator','criticality_denominator'];assert len(values)==2493 and all(all(values[q['connection_id']][f]==q[f] for f in fields) for q in initial)
  w,frame=r['case'].split('/');states=[('source',E/'wbuart_source_checkpoints_v1_2026-10-20'/w/'source/initial.json')] if frame=='source' else [(mode,E/'wbuart_warm_inputs_v1_2026-10-20'/r['case']/mode/'initial.json') for mode in ['raw_min','native_retained']];state_rows=[]
  for mode,p in states:
   records=read(p)['records'];out=model.from_records(records);assert len(out)==2493 and all(out[q['connection_id']]['full_connection_id']==q['full_connection_id'] for q in records);snapshots+=1;connections+=len(out);target=O/r['case']/mode;target.mkdir(parents=True);payload=target/'criticalities.json';payload.write_text(json.dumps(list(out.values()))+'\n');state_rows.append({'mode':mode,'connections':len(out),'changed_from_initialized_baseline':sum(out[cid]['criticality_bits']!=values[cid]['criticality_bits'] for cid in out)});bindings[str(p)]=sha(p);bindings[str(payload)]=sha(payload)
   if negative==0:
    malformed=[dict(q) for q in records];malformed[0]['full_connection_id']+=1
    for bad in [malformed,records[:-1]]:
     try:model.from_records(bad)
     except ValueError:negative+=1
     else:raise AssertionError('Invalid path cohort accepted')
  rows.append({'case':r['case'],'baseline_CIDs':2493,'baseline_bit_mismatches':0,'states':state_rows});print('WBUART_FACTORY_CONTRACT',r['case'],len(states),flush=True)
 try:create(E/'prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/endpoints.json')
 except ValueError:negative+=1
 else:raise AssertionError('Unregistered old-family endpoint accepted')
 assert len(rows)==12 and snapshots==21 and connections==52353 and negative==3
 for n,h in bindings.items():assert sha(Path(n))==h
 result={'status':'ALL12_INITIAL_BASELINES_AND21_CURRENT_PATH_SNAPSHOTS_WITH_STRICT_FACTORY_IDENTITIES_PASS','rows':rows,'baseline_CIDs_checked':29916,'physical_path_snapshots':snapshots,'physical_path_CIDs':connections,'invalid_endpoint_fullCID_and_partial_cohort_rejections':negative,'new_target_route_labels':False,'strict_unseen_admitted':False,'complete_prediction_utility_workflow_admitted':False,'scope':'Exact initialized native baselines; current path snapshots computed by qualified fixed nominal model, not asserted equal to physical native STA after IPIN/pin remap. No quality or full paid gain.','bindings':bindings};(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('WBUART_FACTORY_ALL_PASS',snapshots,connections,flush=True)
if __name__=='__main__':main()
