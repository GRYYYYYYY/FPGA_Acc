"""Whole-cohort local certificate reuse and copied-bundle invalidation probe."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from validated_bundle_certificate import issue,validate,FILES
root=Path(__file__).resolve().parents[1];base=root/'work/gf2_continuous_two_updates_v2_2026-10-06';out=root/'experiments/validated_bundle_certificate_2026-10-06';out.mkdir();cases=[]
for w in [32,64,128]:
 for rd in [0,1]:
  dirs=sorted((base/f'gf2_d{w}'/str(rd)/'experiments').glob('*canonical_reload*'));assert len(dirs)==2
  for parent in dirs:cases.append({'width':w,'round':rd,'parent':str(parent),'receipt_sha256':sha(parent/'receipt.json'),'verification_sha256':sha(parent/'verification.json')})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'sources':{n:sha(root/'tools'/n) for n in ['validated_bundle_certificate.py','trial_validated_bundle_certificate.py']},'scope':'All12 archived canonical candidate/reference bundles; identity copies and one-byte changes to each of4 files. No new native run or owner integration.'},indent=2)+'\n');rows=[]
for i,c in enumerate(cases):
 parent=Path(c['parent']);assert sha(parent/'receipt.json')==c['receipt_sha256'] and sha(parent/'verification.json')==c['verification_sha256'];r=json.loads((parent/'receipt.json').read_text());source=Path(r['results'][0]['cwd'])/'reload';dest=out/str(i);dest.mkdir()
 for n in FILES:shutil.copyfile(source/n,dest/n)
 t=time.monotonic();cert=issue(parent,dest);cpd=validate(cert,dest);elapsed=time.monotonic()-t;rejections=[]
 for n in FILES:
  f=dest/n;original=f.read_bytes();f.write_bytes(original+b'\n')
  try:validate(cert,dest)
  except ValueError:rejections.append(n)
  finally:f.write_bytes(original)
 assert rejections==list(FILES);assert validate(cert,dest)==cpd
 file=dest/'certificate.json';file.write_text(json.dumps(cert,indent=2)+'\n');rows.append({'index':i,'width':c['width'],'round':c['round'],'cpd_ns':cpd,'issue_validate_s':elapsed,'mutations_rejected':rejections,'certificate_sha256':sha(file)})
 print(rows[-1],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'complete':len(rows)==12},indent=2)+'\n')
