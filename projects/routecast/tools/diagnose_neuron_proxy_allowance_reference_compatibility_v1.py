"""Post-label accounting of already-frozen allowance; never calibrates or changes policy."""
import json,resource,hashlib
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def main():
 assert int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())>=30*2**30
 resource.setrlimit(resource.RLIMIT_AS,(768*2**20,768*2**20))
 prereg=R/'experiments/neuron_criticality_proxy_budget_prereg_v1_2026-10-17';proof=json.loads((prereg/'verification.json').read_text());assert proof['all_pass']
 for p,h in proof['bindings'].items():assert sha(Path(p))==h
 native=R/'experiments/neuron_native_proxy_budget_compatibility_v3_2026-10-17';prior=json.loads((native/'verification.json').read_text());assert prior['all_pass']
 rows=native/'reference_rows.jsonl';assert sha(rows)==prior['bindings'][str(rows)]
 budgetfile=prereg/'candidate_budgets.jsonl';budgets={x['connection_id']:x for x in map(json.loads,budgetfile.read_text().splitlines())};assert len(budgets)==77106
 fanout=Counter(x['net'] for x in budgets.values());seen=set();groups={}
 def add(key,oldbad,newbad):
  z=groups.setdefault(key,Counter());z['connections']+=1;z['original_proxy_violations']+=oldbad;z['new_proxy_violations']+=newbad;z['original_violations_now_within_proxy_budget']+=oldbad and not newbad
 for line in rows.open():
  x=json.loads(line);cid=x['connection_id'];assert cid not in seen;seen.add(cid);b=budgets[cid]
  assert (x['net_id'],x['local_sink_pin'],x['floor_integer'],x['budget_integer'])==(b['net'],b['local_sink_pin'],b['floor_integer'],b['original_budget_integer'])
  cost=x['native_path_additive_integer'];oldbad=cost>b['original_budget_integer'];newbad=cost>b['new_budget_integer'];assert not newbad or oldbad
  f=fanout[x['net_id']];kind='fanout1' if f==1 else 'fanout2_to15' if f<16 else 'fanout16_plus'
  for key in ['all',kind]+(['NET'+str(x['net_id'])] if x['net_id'] in [56,1768,21348,21505] else []):add(key,oldbad,newbad)
 assert seen==set(budgets)==set(range(77106)) and groups['all']['original_proxy_violations']==2455
 files=[Path(__file__).resolve(),prereg/'protocol.json',prereg/'verification.json',budgetfile,native/'verification.json',rows]
 out=R/'experiments/neuron_proxy_allowance_reference_compatibility_v1_2026-10-17';out.mkdir()
 result=dict(all_pass=True,all_connections=77106,groups={k:dict(v) for k,v in groups.items()},bindings={str(p):sha(p) for p in files},scope='Post-label development accounting of existing native additive reference paths under the previously frozen allowance. No policy fitting, new native route, model mutation, alternative-path optimality, STA feasibility or prediction improvement established.',promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['groups'],indent=2))
if __name__=='__main__':main()
