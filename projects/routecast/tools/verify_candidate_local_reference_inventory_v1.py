"""Authenticate complete recorded references without claiming a simultaneous snapshot."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];p=R/'experiments/verilog_candidate_local_exposure_v1_2026-10-10/audit.json';v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());ip=R/'experiments/verilog_candidate_origin_inventory_v1_2026-10-10/inventory.json';inventory=json.loads(ip.read_text());assert len(v['rows'])==len(inventory['rows'])==28;assert [x['name'] for x in v['rows']]==[Path(x['path']).name for x in inventory['rows']];owners=defaultdict(set);rows=[]
for row,origin in zip(v['rows'],inventory['rows']):
 assert row['source_sha256']==origin['sha256']==sha(origin['path']);assert row['strict_family_admitted'] is False;assert row['local_reference_detected']==bool(row['local_reference_files']);assert len(set(row['local_reference_files']))==len(row['local_reference_files'])
 for module in origin['declared_module_names']:owners[module].add(row['name'])
 matches=[]
 for rel in row['local_reference_files']:
  f=R/rel;assert str(f) in v['bindings'];assert f.stat().st_size<=2*1024*1024 and f.suffix in ['.py','.json','.md'];s=f.read_text();assert row['name'] in s or row['source_sha256'] in s;matches.append(dict(path=rel,basename_present=row['name'] in s,hash_present=row['source_sha256'] in s))
 rows.append(dict(name=row['name'],all_recorded_references_verified=True,references=matches))
expected=[dict(declared_module=k,files=sorted(vals)) for k,vals in sorted(owners.items()) if len(vals)>1];assert expected==v['shared_declared_module_names'];D=R/'experiments/candidate_local_reference_inventory_verification_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,ip]};assert all(sha(k)==h for k,h in v['bindings'].items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all28_recorded_reference_lists_verified=True,shared_names_verified=len(expected),scope='Every recorded match/hash/source/order/shared-name group checked. Original sequential scan took place during development; absence is neither synchronized filesystem absence nor prior non-exposure. No rerun/global provenance/strict-family admission. LU32 absence cannot override known ongoing LU32 work.'),indent=2)+'\n');print('ALL28 RECORDED REFERENCES VERIFIED',len(expected),'shared names')
