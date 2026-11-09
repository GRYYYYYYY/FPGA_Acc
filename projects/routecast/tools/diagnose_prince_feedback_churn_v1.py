"""Development-only path change census, fixed endpoint dirty groups, no causal claim."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_feedback_churn_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);quality=E/'prince_feedback_quality_v1_2026-10-20/verification.json';v=json.loads(quality.read_text());bindings={str(quality):sha(quality),str(Path(__file__)):sha(__file__)};rows=[]
 for item in v['rows']:
  case=item['case'];width=case.split('/')[0];src=E/'prince_native_source_checkpoints_v1_2026-10-20'/width/'initial.json';endpoint=E/'prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';old={a['connection_id']:a for a in json.loads(src.read_text())['records']};ep=json.loads(endpoint.read_text());dirty={q['net_id'] for q in ep['connections'] if (q['source'],q['sink'])!=(old[q['connection_id']]['source'],old[q['connection_id']]['sink'])};nets={q['net_id'] for q in ep['connections']};arms={}
  for arm in ['raw_min','native_retained']:
   root=E/'prince_feedback_cohort_v1_2026-10-20'/case/arm;initial=root/'initial.json';final=root/'sketch.json';proof=root/'complete_event_audit_v2.json';assert json.loads(proof.read_text())['completed']==len(old);seed={a['connection_id']:a for a in json.loads(initial.read_text())['records']};current={a['connection_id']:a for a in json.loads(final.read_text())['records']};byclass={}
   for name,group in [('endpoint_changed_NETs',dirty),('endpoint_unchanged_NETs',nets-dirty)]:
    cids=[cid for cid,a in current.items() if a['net_id'] in group];seedchanged={current[cid]['net_id'] for cid in cids if current[cid]['answer']['physical_edge_ids']!=seed[cid]['answer']['physical_edge_ids']};sourcechanged={current[cid]['net_id'] for cid in cids if current[cid]['answer']['physical_edge_ids']!=old[cid]['answer']['physical_edge_ids']};byclass[name]=dict(NETs=len(group),CIDs=len(cids),NETs_changed_by_feedback_from_initializer=len(seedchanged),CIDs_changed_by_feedback_from_initializer=sum(current[cid]['answer']['physical_edge_ids']!=seed[cid]['answer']['physical_edge_ids'] for cid in cids),NETs_different_from_source=len(sourcechanged),CIDs_different_from_source=sum(current[cid]['answer']['physical_edge_ids']!=old[cid]['answer']['physical_edge_ids'] for cid in cids))
   arms[arm]=byclass
   for p in [initial,final,proof]:bindings[str(p)]=sha(p)
  for p in [src,endpoint]:bindings[str(p)]=sha(p)
  row=dict(case=case,arms=arms);rows.append(row);print(case,arms['native_retained']['endpoint_unchanged_NETs'],flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Exact frozen endpoint changes identify dirty NETs; full physical-edge-ID list differences counted from initializer and prior source. Descriptive census, not proof changed clean paths cause score regression or local scheduling improves quality.'),indent=2)+'\n')
if __name__=='__main__':main()
