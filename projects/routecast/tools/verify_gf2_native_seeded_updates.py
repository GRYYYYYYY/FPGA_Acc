"""Independent XML replay, native seed path identity, new-search-only bound."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from immutable_xml_prediction_audit import ImmutableXMLAudit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_native_seeded_updates_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'];rows=[]
for case,row in zip(p['cases'],r['rows']):
 assert all(sha(f)==h for f,h in case['inputs_sha256'].items());w=row['width'];d=out/f'gf2_d{w}';assert sha(d/'prior.json')==row['prior_sha256'] and sha(d/'receipt.json')==row['candidate_sha256'];assert not row['repair_invoked'];prior=json.loads((d/'prior.json').read_text());ep=json.loads(Path(case['endpoints']).read_text());xml=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);observed=physical_paths(case['route']);expected={}
 for rec in prior['records']:
  name=ep['net_names'][str(rec['net_id'])];path=[(rec['source'],None)]
  for eid in rec['answer']['physical_edge_ids']:
   edge=xml.graph.edges[eid];assert edge.source==path[-1][0];path.append((edge.sink,edge.switch_id))
  expected.setdefault(name,[]).append(tuple(path))
 assert {n:sorted(paths) for n,paths in observed.items() if paths}=={n:sorted(paths) for n,paths in expected.items()}
 audit=d/'audit';audit.mkdir();protocol={'inputs_sha256':{str(f):sha(f) for f in (d/'prior.json',Path(case['endpoints']),Path(case['swap']))}};(audit/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');inc=json.loads((d/'receipt.json').read_text());inc.update(protocol_sha256=sha(audit/'protocol.json'),source_sha256=sha(root/'tools/trial_gf2_native_seeded_updates.py'));(audit/'incremental.json').write_text(json.dumps(inc,indent=2)+'\n')
 s=(root/'tools/verify_tseng_live_staged_repair_incremental.py').read_text().replace('experiments/tseng_live_staged_repair_2026-10-06',str(audit.relative_to(root))).replace('experiments/tseng_placement_swap_2026-10-06',str(Path(case['swap']).parent.relative_to(root))).replace('experiments/nonzero_rc_tseng_endpoints_2026-10-06',str(Path(case['endpoints']).parent.relative_to(root))).replace("root/'experiments/tseng_joint_transfer_2026-10-06/receipt.json'",'Path('+repr(str(d/'prior.json'))+')').replace('trial_tseng_live_staged_repair.py','trial_gf2_native_seeded_updates.py').replace('assert node==q[\'sink\'] and delay==Fraction(answer[\'delay\'],r[\'scale\'])<=Fraction(1,10**9)',"assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])\n if checkcost:assert delay<=Fraction(1,10**9)").replace('root=Path(__file__).resolve().parents[1]','root=Path('+repr(str(root))+')')
 tool=audit/'audit.py';tool.write_text('import sys\nsys.path.insert(0,'+repr(str(root/'tools'))+')\n'+s)
 with (audit/'audit.log').open('w') as log:code=subprocess.run(['python3',str(tool)],cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0;v=json.loads((audit/'incremental_verification.json').read_text());assert v['accepted_paths_checked']==row['required_connections'];proof={'receipt_sha256':sha(d/'receipt.json'),'accepted_paths_checked':v['accepted_paths_checked'],'audit_sha256':sha(audit/'incremental_verification.json'),'native_seed_exact_physical_paths':True};(d/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');rows.append({'width':w,**proof});print(w,'native seed and staged events verified',flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'rows':rows,'scope':'All native seed printed physical paths matched, independent originalXML retained RC and new-search 1ns/history-cost event replay. Not native updated FULL/STA or accepted publication.'},indent=2)+'\n')
