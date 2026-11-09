"""Coarse identifier-erased lexical shape, collisions require semantic review."""
import json,re,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];p=R/'experiments/verilog_development_module_overlap_v1_2026-10-10/inventory.json';d=json.loads(p.read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert all(sha(k)==h for k,h in d['bindings'].items());bindings={**d['bindings'],str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};groups=defaultdict(list);count=0
for row in d['rows']:
 text=Path(row['path']).read_text(errors='replace');masked=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:' '*len(m[0]),text,flags=re.S);starts=list(re.finditer(r'\bmodule\s+(?:automatic\s+)?([A-Za-z_][A-Za-z_0-9$]*)',masked));ends=list(re.finditer(r'\bendmodule\b',masked));assert len(starts)==len(ends)==row['module_count']
 for a,b in zip(starts,ends):
  body=masked[a.start():b.end()]
  # Every identifier including keywords is erased; deliberately NOT alpha-equivalence.
  tokens=re.findall(r"\d+'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|\d+|[A-Za-z_$][A-Za-z_0-9$]*|[^\s]",body)
  shape=['ID' if re.fullmatch(r'[A-Za-z_$][A-Za-z_0-9$]*',t) else t for t in tokens];h=hashlib.sha256(' '.join(shape).encode()).hexdigest();groups[h].append(dict(family=row['family'],path=row['path'],module=a[1],line=text.count('\n',0,a.start())+1,token_count=len(tokens),identifier_erased_sha256=h));count+=1
collisions=[xs for xs in groups.values() if len({x['family'] for x in xs})>1];assert count==591 and all(sha(k)==h for k,h in bindings.items());D=R/'experiments/benchmark_identifier_shape_screen_v1_2026-10-10';D.mkdir();(D/'screen.json').write_text(json.dumps(dict(bindings=bindings,modules_screened=count,cross_directory_shape_collisions=collisions,strict_family_admitted=False,scope='Coarse comment-masked lexical tokens with all identifiers AND keywords erased. String literals/macros/includes/identifier binding/operator semantics not parsed; repeated-identifier identity not retained. Collisions are only review candidates and may be unrelated logic; absence never proves renamed-module/family independence. Full original paths/lines preserved.'),indent=2)+'\n');print('SHAPE SCREEN',count,'modules',len(collisions),'cross-directory review groups')
