"""Bounded prior-reference and module overlap checks for pinned PRINCE RTL."""
import json,re
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_candidate_source_v2_2026-10-20';D=E/'prince_local_lineage_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=read(S/'verification.json');frontend=E/'prince_source_frontend_v1_2026-10-20/verification.json';proof=read(frontend);assert all(sha(p)==h for p,h in proof['bindings'].items());screenp=E/'local_family_metadata_screen_v1_2026-10-20/verification.json';reviewp=screenp.parent/'research_review_v1.json';screen=read(screenp);review=read(reviewp);rtl=[r for r in source['assets'] if r['relative'].startswith('src/rtl/')];assert len(rtl)==3;hashes={r['sha256']:r['relative'] for r in rtl};alias=re.compile(rb'(?<![A-Za-z0-9_])prince(?:_core|_round_functions)?(?:\.v[h]?)?(?![A-Za-z0-9_])',re.I);matches=[];drift=[];scanned=0
 prior=[(R/r['path'],r['sha256']) for r in screen['metadata']]+[(Path(r['path']),r['sha256']) for r in review['large_metadata_supplement']]
 inventory=E/'ultraembedded_lineage_inventory_v1_2026-10-08/inventory.json';prior.append((inventory,sha(inventory)))
 for p,h in prior:
  b=p.read_bytes()
  if sha(p)!=h:drift.append(str(p));continue
  exact=[name for digest,name in hashes.items() if digest.encode() in b];hit=bool(alias.search(b))
  if exact or hit:matches.append({'path':str(p),'sha256':h,'exact_RTL_hash_references':exact,'alias_reference':hit})
  scanned+=1
 def modules(p):
  t=Path(p).read_text();t=re.sub(r'/\*.*?\*/|//[^\n]*','',t,flags=re.S);return set(re.findall(r'\bmodule\s+(?:automatic\s+)?([A-Za-z_][A-Za-z0-9_$]*)',t))
 candidate=set().union(*(modules(r['path']) for r in rtl));overlaps=[];same=[]
 for row in screen['source_rows']:
  assert sha(row['path'])==row['sha256'];common=sorted(candidate&modules(row['path']))
  if common:overlaps.append({'path':row['path'],'modules':common})
  if row['sha256'] in hashes:same.append(row['path'])
 files=[Path(__file__),S/'verification.json',frontend,screenp,reviewp,inventory,*[Path(r['path']) for r in rtl]];v={'status':'BOUNDED_PINNED_PRINCE_LOCAL_LINEAGE_AUDIT_COMPLETE','revision':source['revision'],'historical_metadata_scanned':scanned,'historical_reference_matches':matches,'metadata_drift':drift,'candidate_modules':sorted(candidate),'local_sources_compared':39,'exact_local_source_matches':same,'module_name_overlaps':overlaps,'strict_unseen_admitted':False,'new_native_labels':False,'bindings':{str(p):sha(p) for p in files},'scope':'Frozen selected historical metadata plus10 large-file supplement and known Ultraembedded inventory;39 local benchmark source comparisons. Exact content/name matching cannot exclude renamed/modified derivatives, other projects, archives, nonJSON or external history. Module names are screening hints, not semantic equivalence or family independence. No routing or training.','next':'Freeze byte-preserving LUT6 compilation and explicit state-boundary/equivalence obligations. Candidate may proceed as prospective local-prepared input with strict family admission still pending; never use native outcomes for candidate selection.'};(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('PRINCE_LOCAL_LINEAGE_COMPLETE',scanned,'references',len(matches),'drift',len(drift),'modules',overlaps,'exact_source',same)
if __name__=='__main__':main()
