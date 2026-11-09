"""Audit completed narrow-width routes against actual XML and endpoint multiset."""
import json,re,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from stream_native_route_audit import audit

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_narrow_success_routes_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_narrow_success_routes.py','stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'widths':[32,64],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'All successful captured native routes, actual XML printed arcs/switches/net-union capacity and retained endpoint multiset; not full electrical or equivalent-pin proof.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for w in protocol['widths']:
  cap=root/f'experiments/multiplier_family_native_capture_cw{w}_2026-10-06';rec=json.loads((cap/'receipt.json').read_text());assert sha(cap/'protocol.json')==rec['protocol_sha256']
  epdir=root/f'experiments/multiplier_cw{w}_reachability_2026-10-06';er=json.loads((epdir/'receipt.json').read_text())
  for case in rec['results']:
   if case['exit_code']!=0:continue
   assert not case['timed_out'];name=case['design'];a=case['artifacts'];assert all(sha(v['path'])==v['sha256'] for v in a.values());epfile=epdir/name/'endpoints.json';epr=next(r for r in er['results'] if r['design']==name);assert sha(epfile)==epr['endpoints_sha256']
   ep=json.loads(epfile.read_text());header=Path(a['design.route']['path']).read_text().splitlines()[0];m=re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',header);assert m and m[1]==a['design.place']['sha256']
   result=audit(a['rr_graph.xml']['path'],a['design.route']['path']);expected=Counter((r['net_id'],r['source'],r['sink']) for r in ep['connections']);nets={r['net_id'] for r in ep['connections']};actual=Counter((r['net_id'],r['source'],r['sink']) for r in result['connections'] if r['net_id'] in nets)
   assert expected==actual and result['overflow_units']==0 and result['all_printed_branch_arc_switch_and_union_checks_pass']
   dest=out/f'cw{w}_{name}';dest.mkdir();(dest/'physical_audit.json').write_text(json.dumps(result)+'\n');row={'width':w,'design':name,'connections':sum(expected.values()),'exact_endpoint_multiset':True,'overflow_units':0,'case_receipt_sha256':sha(cap/(name+'_receipt.json')),'endpoint_receipt_sha256':sha(epdir/'receipt.json'),'physical_audit_sha256':sha(dest/'physical_audit.json')};rows.append(row);print(json.dumps(row),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':rows},indent=2)+'\n')
if __name__=='__main__':main()
