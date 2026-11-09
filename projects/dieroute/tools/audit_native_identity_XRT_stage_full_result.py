"""Terminal full-task emulation review; never accepts budget-only completion."""
import hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/native_identity_XRT_commit_stage_diagnostic_20261015'
def main():
 cache={}
 def sha(f):
  f=Path(f).resolve();key=str(f)
  if key not in cache:
   h=hashlib.sha256()
   with f.open('rb') as v:
    for b in iter(lambda:v.read(1048576),b''):h.update(b)
   cache[key]=h.hexdigest()
  return cache[key]
 def load(f):return json.loads(Path(f).read_text())
 m=load(P/'manifest.json');assert m['status']=='diagnostic_exited_requires_review' and m['returncode']==0,m
 for f in ['protocol.json','launch_protocol.json']:
  for q,h in load(P/f)['source_sha256'].items():assert sha(q)==h,q
 x=load(P/'protocol.json');assert x['maximum_expansions']==2097152 and x['label_capacity']==2097152
 lines=(P/'stdout.log').read_text().splitlines();rows=[]
 for line in lines:
  try:rows.append(json.loads(line))
  except ValueError:pass
 row=next(v for v in rows if v.get('status')=='executed')
 for k,v in x['expected'].items():
  observed=(P/'artifacts/path_nodes.raw').stat().st_size//4 if k=='path_hops' else row[k]
  assert observed==v,(k,observed,v)
 assert (P/'artifacts/path_nodes.raw').stat().st_size%4==0
 assert row['authority_imports']==1 and row['authority_reuploads']==0 and row['verified_upload_bytes']==4482650920
 gold=R/'work/native_policy_identity_ordering_cpu_20261015/identity_higher_g/artifacts'
 compared=[]
 for name in ['attachment.raw','goal.raw','metadata.raw','observations.raw','path_nodes.raw','path_pips.raw','result.raw']:
  assert sha(P/'artifacts'/name)==sha(gold/name),name;compared.append('search/'+name)
 post=R/'work/native_identity_higher_g_commit_differential_20261015/artifacts'
 for name in ['canonical_reads.raw','control.raw','nets.raw','proposal_completion.raw','resources.raw','trees.raw']:
  assert sha(P/'artifacts/commit'/name)==sha(post/name),name;compared.append('commit/'+name)
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes());assert result[0]==0 and result[1]==43
 for f in [P/'manifest.json',P/'protocol.json',P/'launch_protocol.json',P/'stdout.log',P/'run.log',Path(__file__).resolve(),post.parent/'independent_audit.json',gold.parent.parent/'independent_audit.json']:sha(f)
 report=dict(status='full_original_native_task_XRT_search_commit42queries_matches_CPU_search_and_authority_gold',comparisons=compared,execution=row,source_sha256=cache,board_result=False,research_complete=False,scope='Actual linked three-CU hw_emu shared-BO pipeline, one development task. Byte comparison against independently audited CPU search and full authority poststate; no whole-design QoR, physical banks, clock signoff or board performance claim.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(report['status'])
if __name__=='__main__':main()
