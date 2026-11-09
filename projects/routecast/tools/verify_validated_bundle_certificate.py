"""Independent certificate binding and native-log timing audit."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/validated_bundle_certificate_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and len(r['rows'])==len(p['cases'])==12 and r['protocol_sha256']==sha(out/'protocol.json')
for n,h in p['sources'].items():assert sha(root/'tools'/n)==h
for i,(case,row) in enumerate(zip(p['cases'],r['rows'])):
 parent=Path(case['parent']);receipt=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==case['receipt_sha256']==v['receipt_sha256'];assert sha(parent/'verification.json')==case['verification_sha256']
 file=out/str(i)/'certificate.json';assert sha(file)==row['certificate_sha256'];c=json.loads(file.read_text());sr=receipt['results'][0];src=Path(sr['cwd'])/'reload'
 assert c['command']==sr['reload_command'] and c['cpd_ns']==row['cpd_ns']==sr['cpd_ns']
 for n in ['design.blif','design.net','design.place','design.route']:assert sha(out/str(i)/n)==sha(src/n)==c['bundle_hashes'][n]
 for name,h in c['external_hashes'].items():assert sha(name)==h
 assert c['external_hashes'][str(parent/'receipt.json')]==case['receipt_sha256'];assert c['external_hashes'][str(parent/'verification.json')]==case['verification_sha256']
 log=(src/'reload.log').read_text();assert all(x in log for x in ['RouterOpts.check_route: FULL','VPR succeeded','Completed routing consistency check successfully.']);assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1])==c['cpd_ns']
 assert row['mutations_rejected']==list(c['bundle_hashes'])
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'certificates_verified':12,'copied_bundle_files_verified':48,'scope':'Independent source/copy/native log and timing bindings. Mutation probes from runner receipt; no native rerun or owner integration. Caller must bind certificate bytes itself before relying on evidence.'},indent=2)+'\n');print('12 certificates and48 copied files independently verified')
