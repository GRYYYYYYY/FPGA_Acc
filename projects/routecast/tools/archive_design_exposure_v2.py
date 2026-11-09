"""Recursive declared BLIF identity inventory; absence never establishes holdout."""
import json,re,subprocess
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha

def declarations(value,location=()):
 if isinstance(value,dict):
  path=value.get('path')
  if isinstance(path,str) and Path(path).suffix.lower() in ('.blif','.eblif'):
   yield {'json_location':list(location),'path':path,'declared_sha256':value.get('sha256')}
  for key,item in value.items():
   if isinstance(key,str) and Path(key).suffix.lower() in ('.blif','.eblif') and isinstance(item,str) and re.fullmatch('[0-9a-f]{64}',item):
    yield {'json_location':list(location)+( [key]),'path':key,'declared_sha256':item}
   yield from declarations(item,location+(str(key),))
 elif isinstance(value,list):
  for i,item in enumerate(value):yield from declarations(item,location+(str(i),))

def main():
 out=Path('experiments/design_exposure_inventory_v2_2026-10-06');assert not out.exists()
 result=subprocess.run(['rg','--files','--hidden','-g','protocol.json','experiments'],capture_output=True,text=True,check=True)
 paths=sorted(Path(p) for p in result.stdout.splitlines());records=[];unresolved=[];identities=defaultdict(list);protocol_hashes={}
 for p in paths:
  digest=sha(p);data=json.loads(p.read_text());rows=list(declarations(data));protocol_hashes[str(p)]=digest
  if not rows:unresolved.append(str(p))
  for row in rows:
   record={'protocol_path':str(p),'protocol_sha256':digest,**row,'filename_stem':Path(row['path']).stem}
   records.append(record);identity=row['declared_sha256'] or 'unresolved:'+row['path'];identities[identity].append(record)
 assert all(sha(Path(p))==h for p,h in protocol_hashes.items())
 out.mkdir();(out/'source.py').write_bytes(Path(__file__).read_bytes())
 receipt={'source_sha256':sha(__file__),'protocol_count':len(paths),'declared_blif_records':len(records),'filename_stems':sorted({r['filename_stem'] for r in records}),'exposure_by_declared_content_identity':dict(identities),'unresolved_protocols':unresolved,'protocol_sha256':protocol_hashes,'scope':'recursive protocol declarations only; declared hashes are historical identity evidence, not reauthentication of every input or proof of successful use','limitations':['archive absence does not establish unseen status','filename stems and equal architecture are not family identities','family holdout needs dataset provenance and frozen prospective split','unarchived or indirect exposure remains unknown']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['protocol_count','declared_blif_records','filename_stems']}))
if __name__=='__main__':main()
