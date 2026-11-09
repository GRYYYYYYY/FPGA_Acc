"""Archive source-local origin declarations without claiming upstream verification."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks'
D=R/'experiments/local_benchmark_origin_headers_v1_2026-10-10';assert not D.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bindings={str(Path(__file__)):sha(__file__)};rows=[]
for family in ['freecores','ultraembedded']:
 for p in sorted((S/family).glob('*.v')):
  bindings[str(p)]=sha(p)
  # Source declarations anywhere in concatenated benchmark, not just first block.
  evidence=[]
  for line,text in enumerate(p.read_text(errors='replace').splitlines(),1):
   if re.search(r'copyright|author\s*:|https?://|ultra.embedded|this file is part of',text,re.I):
    evidence.append(dict(line=line,text=text))
  rows.append(dict(directory_group=family,file=p.name,path=str(p),sha256=bindings[str(p)],origin_declarations=evidence,upstream_revision_authenticated=False,prior_exposure_cleared=False,heldout_admitted=False))
assert len(rows)==11 and all(sha(p)==h for p,h in bindings.items())
D.mkdir();(D/'inventory.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Exact local declaration lines only, full concatenated source scan. Directory is a collection, not necessarily an independent author/project family. URLs and author strings are source claims; upstream revision/content and global exposure are unverified. Development AES/XTEA/Ethernet/MMC remain exposed; no reclassification.'),indent=2)+'\n')
print(json.dumps([dict(file=x['file'],origin_declaration_lines=len(x['origin_declarations'])) for x in rows],indent=2))
