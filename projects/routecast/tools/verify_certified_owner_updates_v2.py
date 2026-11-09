"""Independent six-snapshot XML/RC/ledger and certificate selection audit."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/certified_owner_updates_v2_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and len(r['rows'])==6 and r['protocol_sha256']==sha(out/'protocol.json')
for n,h in p['sources'].items():assert sha(root/'tools'/n)==h
base=root/'experiments/gf2_continuous_two_updates_v2_2026-10-06';old=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');rows=[]
for row in r['rows']:
 w=row['width'];rev=row['revision'];assert rev==row['round']+1 and row['stale_commit_rejected'] and row['mutation_rejections']==['design.route','certificate.json','selection'];f=out/f'gf2_d{w}_accepted{rev}.json';assert sha(f)==row['snapshot_sha256'];snapshot=json.loads(f.read_text());prior=base/f'gf2_d{w}_accepted{rev}.json';orig=next(c for c in old['rows'] if c['width']==w)['rounds'][rev-1];assert sha(prior)==orig['snapshot_sha256'];assert snapshot==json.loads(prior.read_text())
 values={}
 for label,entry in row['alternatives'].items():
  cp=Path(entry['certificate']);assert sha(cp)==entry['certificate_sha256'];cert=json.loads(cp.read_text());values[label]=cert['cpd_ns']
  for name,h in cert['external_hashes'].items():assert sha(name)==h
  for n,h in cert['bundle_hashes'].items():assert sha(Path(entry['bundle'])/n)==h
 chosen='predicted' if values['predicted']<=values['reference'] else 'reference';assert row['selection']['selected']==chosen and row['selection']['selected_cpd_ns']==values[chosen]
 route=Path(row['alternatives'][chosen]['bundle'])/'design.route';template=(root/'tools/verify_tseng_selected_reference_import.py').read_text();count=len(snapshot['records']);check=template[template.index('def check('):template.index('inc=json.loads')].replace('1234',str(count));tool=out/f'gf2_d{w}_revision{rev}_audit.py'
 text="import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(root/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\nfrom native_route_ledger_import import physical_paths\nfrom pre_route_endpoints import sha\n"+f"snapshot=json.loads(Path({str(f)!r}).read_text());ep=snapshot['endpoint_metadata'];graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+f"paths,ledger=check(snapshot,ep)\nassert paths=={{n:sorted(v) for n,v in physical_paths({str(route)!r}).items() if v}}\n"
 tool.write_text(text);log=tool.with_suffix('.log')
 with log.open('w') as stream:code=subprocess.run(['python3',str(tool)],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0;rows.append({'width':w,'revision':rev,'XML_paths_checked':count,'snapshot_sha256':sha(f),'audit_source_sha256':sha(tool),'audit_log_sha256':sha(log)});print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'Six archived-evidence integration snapshots, originalXML physicalpaths/exactRC/NETunion/ledger and certificate selection verified. Negative probes asserted by producer. No fresh native execution or full update performance claim.'},indent=2)+'\n')
