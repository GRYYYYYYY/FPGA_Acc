"""Conservative lexical overlap evidence, never a heldout certificate."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks'
D=R/'experiments/local_benchmark_module_overlap_v1_2026-10-10';assert not D.exists()
def sha(b):return hashlib.sha256(b).hexdigest()
bindings={str(Path(__file__)):sha(Path(__file__).read_bytes())};rows=[];groups={}
for family in ['freecores','ultraembedded']:
 files=sorted((S/family).glob('*.v'));assert files
 for p in files:
  raw=p.read_bytes();bindings[str(p)]=sha(raw);text=raw.decode('utf-8',errors='replace')
  # Comment masking keeps positions; lexical screening only, not a Verilog parser.
  masked=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:' '*len(m[0]),text,flags=re.S)
  starts=list(re.finditer(r'\bmodule\s+(?:automatic\s+)?([A-Za-z_][A-Za-z_0-9$]*)',masked));ends=list(re.finditer(r'\bendmodule\b',masked))
  assert len(starts)==len(ends),(p,len(starts),len(ends))
  modules=[]
  for i,(a,b) in enumerate(zip(starts,ends)):
   assert a.end()<b.start() and (i+1==len(starts) or b.end()<starts[i+1].start())
   # Whitespace/comment normalization retains identifier names and all tokens.
   tokens=re.findall(r'\S+',masked[a.start():b.end()]);h=sha(' '.join(tokens).encode())
   entry=dict(family=family,path=str(p),module=a[1],line=text.count('\n',0,a.start())+1,lexical_sha256=h)
   modules.append(entry);groups.setdefault(h,[]).append(entry)
  rows.append(dict(family=family,path=str(p),sha256=bindings[str(p)],module_count=len(modules),modules=modules))
shared=[v for v in groups.values() if len({x['family'] for x in v})>1]
assert all(sha(Path(p).read_bytes())==h for p,h in bindings.items())
D.mkdir();out=dict(bindings=bindings,rows=rows,cross_directory_identical_lexical_modules=shared,strict_heldout_admitted=False,scope='All local top-level .v files in two benchmark directories; identical comment-masked whitespace-normalized module text is overlap evidence only. String literals, macros, include expansion, aliases, renamed/rewritten modules, global history and upstream lineage are not resolved. Absence of matches never certifies independent families. No files modified outside RouteCast.')
(D/'inventory.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(files=len(rows),modules=sum(x['module_count'] for x in rows),cross_directory_groups=len(shared),strict_heldout_admitted=False),indent=2))
