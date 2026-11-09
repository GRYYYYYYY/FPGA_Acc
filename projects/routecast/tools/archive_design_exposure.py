"""Conservative archive inventory; absence is not proof of unseen status."""
import json
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/design_exposure_inventory_2026-10-05')
if out.exists():raise ValueError('fresh output required')
paths=sorted(set(Path('experiments').glob('*/protocol.json'))|set(Path('experiments').glob('*/*/protocol.json')))
records=[];designs={};unresolved=[]
for p in paths:
 data=json.loads(p.read_text());inputs=data.get('inputs',{})
 entry=inputs.get('blif') if isinstance(inputs,dict) else None
 if isinstance(entry,dict) and isinstance(entry.get('path'),str):
  design=Path(entry['path']).stem;record={'protocol_path':str(p),'protocol_sha256':sha(p),'declared_blif_path':entry['path'],'declared_blif_sha256':entry.get('sha256'),'design_filename_stem':design}
  designs.setdefault(design,[]).append(record);records.append(record)
 else:unresolved.append({'protocol_path':str(p),'protocol_sha256':sha(p),'reason':'no direct inputs.blif.path; filename alone not treated as identity'})
out.mkdir();(out/'source.py').write_text(Path(__file__).read_text())
receipt={'scope':'all currently present experiments/*/protocol.json and experiments/*/*/protocol.json; direct BLIF declarations only','source_sha256':sha(__file__),'protocol_count':len(paths),'direct_blif_record_count':len(records),'design_filename_stems':sorted(designs),'exposure_by_design':designs,'unresolved_protocols':unresolved,'limitations':['archive presence means historical exposure, not necessarily successful evaluation','missing BLIF declaration or deeper/unarchived activity prevents claiming a design unseen','filename stem is not design-family identity; family split requires dataset provenance and a prospective frozen manifest','ongoing experiments are included only if protocol exists at inventory time']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ('protocol_count','direct_blif_record_count','design_filename_stems')}))
