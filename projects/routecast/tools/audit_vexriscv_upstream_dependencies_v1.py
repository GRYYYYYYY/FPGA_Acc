"""Read-only local dependency search plus pinned upstream tree/source hash audit."""
import json,hashlib,urllib.request,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_upstream_dependencies_v1_2026-10-09';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=E/'prospective_family_candidates_2026-10-06/manifest.json';rows=[r for r in json.loads(m.read_text())['records'] if r['family_candidate']=='vexriscv'];base=Path(rows[0]['original_path']).parents[3];revision='8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';report=dict(bindings={str(m):sha(m),str(Path(__file__).resolve()):sha(__file__)},revision=revision,upstream_authenticated=False)
url='https://api.github.com/repos/verilog-to-routing/vtr-verilog-to-routing/git/trees/'+revision+'?recursive=1'
(D/'protocol.json').write_text(json.dumps(dict(url=url,timeout_s=30,policy='No arbitrary initialization replacement or missing-module stub. Freeze dependency findings only.'),indent=2)+'\n')
try:
 with urllib.request.urlopen(url,timeout=30) as response:data=response.read()
 (D/'tree.json').write_bytes(data);tree=json.loads(data);assert tree['sha']==revision and not tree.get('truncated');report['upstream_authenticated']=True;paths=[x['path'] for x in tree['tree'] if x['type']=='blob'];report['vexriscv_files']=[p for p in paths if '/vexriscv/' in p];report['initialization_files']=[p for p in paths if 'VexRiscv' in p or 'Murax' in p or 'Briey' in p if p.endswith('.bin')]
 matches=[]
 for row in rows:
  relative='vtr_flow/benchmarks/vexriscv/'+Path(row['original_path']).name
  url='https://raw.githubusercontent.com/verilog-to-routing/vtr-verilog-to-routing/'+revision+'/'+relative
  with urllib.request.urlopen(url,timeout=30) as response:source=response.read()
  digest=hashlib.sha256(source).hexdigest();matches.append(dict(member=Path(relative).stem,upstream_sha256=digest,local_sha256=row['sha256'],matches=digest==row['sha256']))
  print(matches[-1]['member'],matches[-1]['matches'],flush=True)
 report['members']=matches
except Exception as error:report['error']=repr(error)
report['scope']='Pinned upstream tree/source content authentication only; no global unseen-family, sequential equivalence, initialization semantics or timing claim.'
report['files']={str(p):sha(p) for p in D.iterdir() if p.is_file()};(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','members','files','vexriscv_files')},flush=True)
