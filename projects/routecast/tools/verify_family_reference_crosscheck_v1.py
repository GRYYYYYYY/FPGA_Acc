"""Full-regex versus byte-indexed/pruned reference scan reconciliation."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';A=E/'preroute_family_admission_v1_2026-10-20';B=E/'preroute_family_reference_crosscheck_v2_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 a=load(A/'family_audit_v1.json');b=load(B/'family_audit_v1.json');assert a['rows']==b['rows'];assert a['scanned_files']==b['scanned_files']==15051;assert a['excluded_files']==b['excluded_files']==181
 for p,h in b['bindings'].items():assert sha(p)==h
 digests=load(B/'scanned_file_digests.json');assert len(digests)==b['scanned_files'];changed=[]
 for p,h in digests.items():
  if sha(p)!=h:changed.append(p)
 assert not changed,changed
 source_count=sum(len(r['sources']) for r in a['rows']);assert source_count==65 and len(a['rows'])==22
 old=load(E/'design_exposure_inventory_v3_2026-10-15/research_decision_v1.json');known={r['declared_sha256'] for r in old.get('candidate_status',[])};prior_exact=sum(s['sha256'] in known for r in a['rows'] for s in r['sources'])
 out=dict(status='BOTH_REFERENCE_SCANS_MATCH_ALL22_GROUPS_AND65_SOURCE_DESCRIPTORS',scanned_files=len(digests),excluded_files=181,groups=22,sources=65,sources_matching_prior_28entry_catalog=prior_exact,all_groups_have_prior_reference=all(r['reference_count']>0 for r in a['rows']),strict_unseen_admitted=0,scope='Bounded reference audit only. Conservativefolder grouping is not functional-family equivalence;prior references are not necessarily model/route/label exposure. No-reference or uncataloguedvariant cannot certify newheldoutfamily.',bindings={str(p):sha(p) for p in [A/'family_audit_v1.json',B/'family_audit_v1.json',B/'scanned_file_digests.json',Path(__file__)]})
 with (A/'family_reference_crosscheck_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'],prior_exact)
if __name__=='__main__':main()
