"""Authenticate finished trials and retain strict canonical failure, without retroactive acceptance."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_ignored_interface_summary_v1_2026-10-08';out.mkdir();bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
identity=R/'experiments/aes_ignored_identity_v1_2026-10-08/receipt.json';idata=json.loads(identity.read_text());bindings[str(identity)]=sha(identity)
for folder in ['aes_ignored_seed_admission_v1_2026-10-08','aes_cold_partition_audit_v1_2026-10-08']:
 receipt=R/'experiments'/folder/'receipt.json';data=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings[str(receipt)]=sha(receipt)
 for row in data['rows']:
  assert all(sha(k)==v for k,v in row['files'].items());name=row['name'];w=receipt.parent/name;logpath=receipt.parent/(name+'_canonical')/'reload.log';log=logpath.read_text();bindings[str(logpath)]=sha(logpath)
  counts=next(x for x in idata['results'] if x['name']==name);part=json.loads((w/'partition.json').read_text());whole=set(part['all_connection_ids']);physical=set(part['physical_connection_ids']);ignored=set(part['ignored_connection_ids']);assert not physical&ignored and physical|ignored==whole and len(whole)==counts['all_queries'] and len(ignored)==counts['native_ignored_queries']
  audit=json.loads((w/'audit.json').read_text());assert audit['overflow_units']==0
  mismatches=int(re.search(r'Found (\d+) mismatches',log)[1]);fixups=int(re.search(r'Fixed (\d+) routing traces',log)[1]);cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);assert row['native_exit_code']==0 and 'VPR succeeded' in log and cpd==row['cpd_ns'] and mismatches==fixups==len(ignored)
  rows.append({'trial':folder,'name':name,'native_route_and_physical_audit_pass':True,'all_queries_accounted':True,'all_queries':len(whole),'physical_queries':len(physical),'native_ignored_queries':len(ignored),'cpd_ns':cpd,'wirelength':row['wirelength'],'canonical_cpd_equal':True,'canonical_mismatches':mismatches,'canonical_fixups':fixups,'strict_zero_fixup_canonical_pass':False})
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'limitations':['Count equality does not independently identify every canonical remapping as ignored; original zero-fixup gate stays failed.','Archive reuse admission repair is not a fresh complete model workflow timing result.','Original HDL semantic relation and unseen-family validation remain unproven.','No final QoR or full workflow speed success claimed.']},indent=2)+'\n');print(json.dumps(rows,indent=2))
