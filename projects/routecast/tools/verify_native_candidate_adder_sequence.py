import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_adder_sequence_2026-10-06';work=root/'work/native_candidate_adder_sequence_2026-10-06';r=json.loads((out/'receipt.json').read_text());rows={x['case']:x for x in r['results']};files=[out/'receipt.json',Path(r['command'][0])]
def locations(path):
 result={}
 for line in path.read_text().splitlines():
  fields=line.split()
  if len(fields)==6 and fields[-1].startswith('#'):
   result[int(fields[-1][1:])]=tuple(map(int,fields[1:5]))
 return result
for name,row in rows.items():
 assert row['exit_code']==0 and all(sha(p)==h for p,h in row['inputs_sha256'].items());cwd=work/name;case=out/name;log=(case/'run.log').read_text();seq=row['sequence'];numbers=list(map(int,row['pairs'].split()));pairs=list(zip(numbers[::2],numbers[1::2]));expected=locations(cwd/'design.place')
 for decision,(a,b) in zip(seq,pairs):
  if decision=='A':expected[a],expected[b]=expected[b],expected[a]
 assert expected==locations(cwd/'accepted.place')
 assert re.findall(r'selected move pair step=(\d+) blocks=(\d+),(\d+)',log)==[(str(i),str(a),str(b)) for i,(a,b) in enumerate(pairs)]
 assert log.count('moved candidate passed native FULL routing check')==len(seq)
 assert log.count('restored delay matrix and all edge-delay/STA metric observations')==seq.count('R')
 armed=re.findall(r'armed context-bound candidate sync ticket epoch=(\d+)',log);consumed=re.findall(r'consume context-bound candidate sync ticket epoch=(\d+)',log);assert armed==consumed==list(map(str,range(1,len(armed)+1)))
 assert sha(cwd/'output.route')==row['route_sha256'] and sha(cwd/'design.net.post_routing')==row['packed_sha256'];assert sha(case/'run.log')==row['log_sha256']
 files.extend(p for p in cwd.iterdir() if p.is_file());files.extend(p for p in case.iterdir() if p.is_file())
for a,b in [('two','two_reject'),('overlap','overlap_reject')]:
 for f in ('accepted.place','output.route','design.net.post_routing'):assert (work/a/f).read_bytes()==(work/b/f).read_bytes()
 assert rows[a]['cpd_ns']==rows[b]['cpd_ns']
(out/'verification.json').write_text(json.dumps({'cases':len(rows),'candidate_steps':sum(len(x['sequence']) for x in rows.values()),'sha256':{str(p):sha(p) for p in files},'checks':['accepted placement matches sequential swaps for all blocks','different and overlapping block pairs selected as declared','all candidate FULL gates and ticket epochs checked','two independent rejection-prefix byte comparisons'],'scope':'adder_tree_2L_032bits canonical snapshot; previously used research family, CLBs 0..4 only; each candidate cold routed; not heterogeneous sites/macros or performance evidence.'},indent=2)+'\n');print('verified')
