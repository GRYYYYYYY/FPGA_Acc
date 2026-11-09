"""Snapshot scoped prior-use evidence before candidate frontend/route labels."""
import subprocess,json,hashlib,re,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks/ultraembedded';D=R/'experiments/ultraembedded_lineage_inventory_v1_2026-10-08';assert not D.exists()
files=subprocess.run(['rg','--files','experiments','tools','-g','*protocol*.json','-g','*receipt*.json','-g','*manifest*.json','-g','*admission_review*.json','-g','*.py'],cwd=R,capture_output=True,text=True,check=True).stdout.splitlines();files += ['RESEARCH_PLAN.md','README.md'];files=sorted(set(files));files=[f for f in files if Path(f).name!=Path(__file__).name]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
candidates=[]
for path in sorted(source.glob('*.v')):
 text=path.read_text();mods=re.findall(r'^\s*module\s+([A-Za-z_][A-Za-z_0-9]*)',text,re.M);candidates.append(dict(filename=path.name,path=str(path),sha256=sha(path),bytes=path.stat().st_size,modules=mods,prior_exact_filename_or_source_hash_hits=[]))
snapshot=[];family_hits=[]
for f in files:
 path=R/f;raw=path.read_bytes();text=raw.decode('utf-8',errors='replace');snapshot.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
 if 'ultraembedded' in text:family_hits.append(str(path))
 for c in candidates:
  found=[x for x in [c['filename'],c['sha256']] if x in text]
  if found:c['prior_exact_filename_or_source_hash_hits'].append(dict(path=str(path),matched_identifiers=found))
D.mkdir();(D/'inventory.json').write_text(json.dumps(dict(source_project_family='ultraembedded',candidates=candidates,prior_project_family_marker_hits=family_hits,searched_files=snapshot,searched_total_bytes=sum(x['bytes'] for x in snapshot),search_scope='RouteCast local Python tools plus experiment protocol/receipt/manifest/admission-review JSON and journal/README, snapshot before candidate frontends. Source filename/hash and project family markers only.',limitations='No global prior-use/alias/content-equivalence proof. Does not cover every raw log/route/BLIF or external/TilePlace experimental history. All ultraembedded files grouped as ONE upstream family, not independent heldout families; shared modules/domain overlap unresolved. Inventory alone never establishes strict unseen family.'),indent=2)+'\n');print(json.dumps(dict(candidates=[dict(filename=c['filename'],hits=len(c['prior_exact_filename_or_source_hash_hits']),modules=len(c['modules'])) for c in candidates],family_marker_hits=len(family_hits),files=len(snapshot),bytes=sum(x['bytes'] for x in snapshot)),indent=2),flush=True)
