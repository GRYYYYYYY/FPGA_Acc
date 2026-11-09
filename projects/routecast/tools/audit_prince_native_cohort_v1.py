"""Independently audit physical trees and pre-route endpoint identity; retain all cases."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import extract,sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];O=R/'experiments/prince_native_cohort_v1_2026-10-20'
def main():
 pp=O/'protocol.json';p=json.loads(pp.read_text());receipt=O/'receipt.json';allrows=json.loads(receipt.read_text());rows=[]
 assert len(allrows['results'])==12 and all(sha(f)==h for f,h in p['bindings'].items())
 for job in p['jobs']:
  d=Path(job['directory']);rp=d/'receipt.json';r=json.loads(rp.read_text());assert all(sha(f)==h for f,h in r['files'].items());row={'case':job['case'],'native_full_check_pass':r['native_full_check_pass'],'eligible_legal_label':False,'canonical_reload_pending':r['native_full_check_pass']};graph=d/'rr_graph.xml';route=d/'output.route'
  try:
   physical=audit(graph,route);(d/'physical_audit.json').write_text(json.dumps(physical)+'\n');ep,report=extract(d/'design.net',d/'design.place',graph);(d/'pre_route_endpoints.json').write_text(json.dumps(ep)+'\n')
   names={int(x[1]):x[2] for line in route.read_text().splitlines() if (x:=NET.match(line))};expected=Counter((ep['net_names'][str(c['net_id'])],c['source'],c['sink']) for c in ep['connections']);observed=Counter((names[c['net_id']],c['source'],c['sink']) for c in physical['connections']);assert expected==observed,'pre-route terminal mismatch'
   row.update(physical_tree_endpoint_audit_pass=True,connections=len(ep['connections']),overflow_units=physical['overflow_units'],eligible_legal_label=r['native_full_check_pass'] and physical['overflow_units']==0)
  except Exception as exc:row.update(physical_tree_endpoint_audit_pass=False,error=repr(exc))
  row['bindings']={str(f):sha(f) for f in [rp,graph,route] if f.exists()};rows.append(row);print('PHYSICAL_AUDIT',row['case'],row['eligible_legal_label'],row.get('error',''),flush=True)
 assert all(sha(f)==h for f,h in p['bindings'].items())
 result=dict(rows=rows,legal_native_and_physical_cases=sum(x['eligible_legal_label'] for x in rows),required_cases=12,required_target_cases=9,canonical_reload_complete=False,strict_unseen_admitted=False,bindings={str(f):sha(f) for f in [pp,receipt,Path(__file__)]},scope='Physical printed arcs/switches/capacity and exact pre-route endpoint multisets. Failed/overused routes retained as diagnostics only. Canonical reload, forecast evaluation and full-paid utility remain open; no physical reset/timing or unseen claims.')
 (O/'independent_physical_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
