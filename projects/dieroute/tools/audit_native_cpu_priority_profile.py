"""Review CPU-only popped-priority logging against the frozen full-search reference."""
import csv,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_fullgraph_cpu_priority_profile_20261015';B=R/'work/native_fullgraph_cpu_full_search_20261015'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as v:
  for b in iter(lambda:v.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['returncode']==0 and m['status']=='terminal_requires_review'
 for field in ['source_sha256','input_source_sha256']:
  for f,h in p[field].items():assert sha(f)==h,f
 comparisons=[]
 for f in (B/'artifacts').glob('*.raw'):
  q=P/'artifacts'/f.name;assert sha(f)==sha(q),f;comparisons.append(f.name)
 assert len(comparisons)==7
 modified=[]
 for f in (P/'include').glob('*.hpp'):
  before=(B/'include'/f.name).read_text();after=f.read_text()
  if before!=after:
   assert f.name=='native_search_hbm_snapshot_search_sharded.hpp'
   assert after.replace('\n  DIEROUTE_CPU_PRIORITY_OBSERVE(current.cost,potential?potential[current.node]:0);','')==before
   modified.append(f.name)
 assert len(modified)==1
 with (P/'artifacts/priority_profile.tsv').open() as f:counts={int(v['priority']):int(v['count']) for v in csv.DictReader(f,delimiter='\t')}
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes());goal=struct.unpack('<8Q',(P/'artifacts/goal.raw').read_bytes());assert result[0]==0 and sum(counts.values())==result[1]==229746 and max(counts)==goal[1]==42
 files=[P/'protocol.json',P/'manifest.json',P/'artifacts/priority_profile.tsv',P/'oracle.cpp',P/'include'/modified[0],Path(__file__).resolve()]
 report=dict(status='CPU_priority_logging_preserves_seven_reference_artifacts',expanded=result[1],priority_counts=counts,goal_cost=goal[1],equal_goal_priority_expansions=counts[42],lower_priority_expansions=sum(n for f,n in counts.items() if f<42),equal_goal_priority_fraction=counts[42]/result[1],artifact_comparisons=comparisons,source_sha256={str(f):sha(f) for f in files},scope='One original full task, same observed path/journal/counters after CPU-only logging. Large equal-goal-priority population motivates tie-order diagnosis, not proof a different order improves search, quality or hardware. Remaining lower-f expansions cannot be removed by equal-f tie order alone.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
