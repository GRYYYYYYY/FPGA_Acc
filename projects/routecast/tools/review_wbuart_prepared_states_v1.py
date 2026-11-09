"""All-CID/proxy-budget parity and retention review, no target labels."""
import hashlib,json,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'experiments/wbuart_source_checkpoints_v1_2026-10-20';W=R/'experiments/wbuart_warm_inputs_v1_2026-10-20';F=R/'experiments/wbuart_frame_raw_floors_v1_2026-10-20';O=R/'experiments/wbuart_prepared_states_review_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);st=json.loads((S/'terminal.json').read_text());wt=json.loads((W/'terminal.json').read_text());assert st['all_pass'] and wt['all_pass'] and len(st['rows'])==3 and len(wt['rows'])==9
 bindings={str(p):sha(p) for p in [Path(__file__),S/'terminal.json',W/'terminal.json',F/'independent_cache_origin_verification_v1.json']};rows=[];pairs=0;totalfallback=0
 for w in [96,128,160]:
  sp=S/f'w{w:03d}/source';source=json.loads((sp/'initial.json').read_text());sproof=json.loads((sp/'independent_xml_verification_v1.json').read_text());assert source['graph_sha256']==json.loads((F/f'w{w:03d}/source/verification.json').read_text())['graph_sha256'];assert source['history']=={} and source['overflow_units']==0 and len(source['records'])==2493
  for n,h in sproof['bindings'].items():assert sha(Path(n))==h
  bindings[str(sp/'independent_xml_verification_v1.json')]=sha(sp/'independent_xml_verification_v1.json');old={r['connection_id']:r for r in source['records']}
  for i in [1,2,3]:
   case=f'w{w:03d}/episode_{i:02d}';frames={};details={}
   for mode in ['raw_min','native_retained']:
    d=W/case/mode;vp=d/'verification.json';v=json.loads(vp.read_text());assert v['connections']==2493 and v['native_staged_state_independent_xml_pass']
    for n,h in v['bindings'].items():assert sha(Path(n))==h
    frame=json.loads((d/'initial.json').read_text());frame_rows={r['connection_id']:r for r in frame['records']};assert set(frame_rows)==set(old)==set(range(2493));assert frame['graph_sha256']==source['graph_sha256'] and frame['history']=={}
    assert all(r['full_connection_id']==old[cid]['full_connection_id'] for cid,r in frame_rows.items());frames[mode]=frame_rows;bindings[str(vp)]=sha(vp);events=json.loads((d/'initializer_events.json').read_text());fallback=sum(bool(e['whole_NET_fallback']) for e in events) if mode=='native_retained' else None
    if fallback is not None:totalfallback+=fallback
    details[mode]={'dirty_nets':len(v['dirty_nets']),'overflow_units':frame['overflow_units'],'whole_NET_fallbacks':fallback}
   for cid,r in frames['raw_min'].items():
    q=frames['native_retained'][cid];assert all(r[k]==q[k] for k in ['net_id','source','sink','full_connection_id','floor_integer','proxy_budget_integer','budget_integer']);pairs+=1
   changed=[cid for cid,r in frames['native_retained'].items() if (r['source'],r['sink'])!=(old[cid]['source'],old[cid]['sink'])];unchanged=set(old)-set(changed);retained=sum(frames['native_retained'][cid]['answer']==old[cid]['answer'] for cid in unchanged)
   assert len(changed)=={1:94,2:17,3:62}[i];rows.append({'case':case,'changed_endpoints':len(changed),'unchanged_endpoints':len(unchanged),'unchanged_paths_retained':retained,'initializers':details})
 assert pairs==22437 and len(rows)==9
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ALL3_SOURCE_AND18_WARM_INPUTS_CID_PROVENANCE_AND22437_MATCHED_BUDGET_PAIRS_VERIFIED','source_connections':7479,'warm_connections':44874,'paired_budget_checks':pairs,'native_whole_NET_fallbacks':totalfallback,'rows':rows,'new_target_route_labels':False,'strict_unseen_admitted':False,'timing_inputs_ready':False,'complete_prediction_utility_workflow_admitted':False,'scope':'Input correctness and prospective budget parity only. Warm cross-NET overflow allowed, not native feasibility or predictor quality. All source/floor/setup/audit costs remain paid dependencies.','next':'Capture and independently validate all12 current native initialized timing/pin/atom inputs and three graph-native node-price domains, without source→target timing substitution; freeze full prediction/control/ablation/native-utility before target labels.','bindings':bindings};(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PREPARED_STATES_REVIEW_PASS',pairs,'fallbacks',totalfallback);print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
