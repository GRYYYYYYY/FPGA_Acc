"""Independent physical arc/branch/uniqueNET occupancy and endpoint audit, failures retained."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_search_attempt_trial_v1_2026-10-20';E=R/'experiments'
def main():
 pp=D/'protocol.json';p=json.loads(pp.read_text());vp=D/'verification.json';v=json.loads(vp.read_text());bycase={x['case']:x for x in v['rows']};bindings={str(x):sha(x) for x in [pp,vp,Path(__file__)]};rows=[]
 for job in p['jobs']:
  case=job['case'];base=case.rsplit('/',1)[0];d=Path(job['directory']);r=dict(bycase[case]);text=(d/'native.log').read_text();r['native_full_check_pass']=r['native_exit_code']==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;row=dict(case=case,native_full_check_pass=r['native_full_check_pass'],eligible_legal_label=False)
  try:
   graph=Path(job['command'][job['command'].index('--read_rr_graph')+1]);route=d/'output.route';assert sha(route)==r['files'][str(route)];physical=audit(graph,route);out=d/'physical_audit.json';assert not out.exists();out.write_text(json.dumps(physical)+'\n');ep=E/'prince_native_cohort_v1_2026-10-20'/base/'pre_route_endpoints.json';e=json.loads(ep.read_text());assert e['graph_sha256']==sha(graph);assert sha(d/'design.net')==e['inputs']['net']['sha256'] and sha(d/'design.place')==e['inputs']['place']['sha256'];names={int(x[1]):x[2] for line in route.read_text().splitlines() if (x:=NET.match(line))};expected=Counter((e['net_names'][str(x['net_id'])],x['source'],x['sink']) for x in e['connections']);observed=Counter((names[x['net_id']],x['source'],x['sink']) for x in physical['connections']);assert expected==observed
   row.update(physical_tree_endpoint_audit_pass=True,connections=len(e['connections']),overflow_units=physical['overflow_units'],eligible_legal_label=r['native_full_check_pass'] and physical['overflow_units']==0)
   for q in [graph,route,ep,out]:bindings[str(q)]=sha(q)
  except Exception as exc:row.update(physical_tree_endpoint_audit_pass=False,error=repr(exc))
  rows.append(row);print('ORACLE_PHYSICAL',case,row['eligible_legal_label'],row.get('overflow_units'),row.get('error',''),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'independent_physical_verification_v1.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='All failures retained; physical audit does not upgrade failed/overused native runs to legal labels.'),indent=2)+'\n')
if __name__=='__main__':main()
