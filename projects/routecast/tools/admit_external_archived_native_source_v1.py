"""Admit an existing native source outcome without rerouting or replacing failures."""
import argparse,json
from pathlib import Path
from pre_route_endpoints import sha

def admit(manifest,case):
    m=json.loads(Path(manifest).read_text())
    if not all(sha(p)==h for p,h in m['bindings'].items()):raise ValueError('archive manifest drift')
    rows=[r for r in m['cases'] if r['case']==case]
    if len(rows)!=1:raise ValueError('archive case')
    p=Path(rows[0]['output'])/'verification.json';v=json.loads(p.read_text())
    if not all(sha(q)==h for q,h in v['bindings'].items()):raise ValueError('archive proof drift')
    if v['status']!='FULL_PHYSICAL_AND_CANONICAL_PASS':raise ValueError('archived source unavailable: '+case)
    if not v['canonical']['semantic_consistency_gate_pass'] or not all(sha(q)==h for q,h in v['canonical']['files'].items()):raise ValueError('canonical source drift')
    return case
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('case');a=p.parse_args();print('ARCHIVED_NATIVE_SOURCE_ADMITTED',admit(a.manifest,a.case))
