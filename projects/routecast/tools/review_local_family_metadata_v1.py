"""Reauthenticate sources and supplement omitted large files plus known inventory."""
import json,re
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'local_family_metadata_screen_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'verification.json';v=read(p);inventory=E/'ultraembedded_lineage_inventory_v1_2026-10-08/inventory.json';prior=read(inventory);extra=[];bindings={str(q):sha(q) for q in [p,inventory,Path(__file__)]};verified=[]
 for row in v['source_rows']:
  assert sha(row['path'])==row['sha256'];witnesses=[]
  if row['references']:
   witness=row['references'][0];mp=R/witness['metadata'];assert sha(mp)==witness['metadata_sha256'];data=mp.read_text();assert row['sha256'] in data or re.search(r'(?<![A-Za-z0-9_])'+re.escape(row['filename'])+r'(?![A-Za-z0-9_])',data,re.I);witnesses.append({'path':str(mp),'kind':'selected_metadata_reference'});bindings[str(mp)]=sha(mp)
  for candidate in prior['candidates']:
   if candidate['sha256']==row['sha256']:assert candidate['filename']==row['filename'];witnesses.append({'path':str(inventory),'kind':'historical_exact_source_inventory_entry'})
  verified.append({'filename':row['filename'],'source':row['path'],'sha256':row['sha256'],'reference_witnesses':witnesses,'strict_unseen_admitted':False})
 for omitted in v['unresolved']:
  mp=R/omitted['path'];data=mp.read_bytes();lower=data.lower();matches=[]
  for row in v['source_rows']:
   byname=row['filename'].encode().lower() in lower;byhash=row['sha256'].encode() in data
   if byname or byhash:matches.append({'filename':row['filename'],'filename_substring_hint':byname,'exact_sha256_reference':byhash})
  extra.append({'path':str(mp),'bytes':len(data),'sha256':sha(mp),'matches':matches,'scope':'Supplementary substring/digest hints; no absence-to-unseen or actual label exposure inference.'});bindings[str(mp)]=sha(mp)
 assert len(verified)==39 and all(r['reference_witnesses'] for r in verified)
 result={'status':'ALL39_LOCAL_SOURCES_HAVE_HISTORICAL_REFERENCE_WITNESSES_LARGE_METADATA_SUPPLEMENTED','rows':verified,'large_metadata_supplement':extra,'previous_no_reference_count':3,'resolved_by_historical_exact_inventory':3,'strict_unseen_families_admitted':0,'bindings':bindings,'scope':'Every source reauthenticated and at least one historical reference validated. This proves historical declaration/reference, not that every candidate was used for training or labels. All10 previously omitted files now scanned for hints, but no claim of complete tools/nonJSON/project/global/derivative history. No synthesis/place/route/label production.','next':'Do not select any of these39 by absence in the earlier bounded screen. Prospective external source acquisition needs a separate pre-acquisition lineage/exposure scope and pinned revision, before compile/place/route outcomes; no automatic unseen claim.'};out=D/'research_review_v1.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print('ALL39_HISTORICAL_REFERENCE_WITNESSES_VERIFIED','large_files',len(extra))
if __name__=='__main__':main()
