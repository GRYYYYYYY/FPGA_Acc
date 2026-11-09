"""Review complete or bounded full-native two-phase XRT run without extrapolation."""
import hashlib,json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_two_phase_identity_XRT_pipeline_20261015'
def main():
 refs={}
 def sha(f):
  f=Path(f).resolve();key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with f.open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 def load(f):return json.loads(Path(f).read_text())
 x=load(P/'protocol.json');m=load(P/'manifest.json')
 assert m['status'] in ['diagnostic_exited_requires_review','bounded_diagnostic_not_completed'],m
 assert x['maximum_probe_wall_seconds']==1800 and x['maximum_expansions']==x['label_capacity']==2097152
 for name in ['protocol.json','launch_protocol.json','image_binding.json']:
  for f,h in load(P/name)['source_sha256'].items():assert sha(f)==h,f
 host=(P/'source/tb/host.cpp').read_text()
 for c in reversed(load(P/'wait_observation_changes.json')):
  assert host.count(c['after'])==1;host=host.replace(c['after'],c['before'],1)
 parent=R/'work/native_identity_XRT_commit_stage_diagnostic_20261015/source/tb/host.cpp';assert host==parent.read_text()
 searchgold=R/'work/native_policy_identity_ordering_cpu_20261015/identity_higher_g/artifacts';postgold=R/'work/native_identity_higher_g_commit_differential_20261015/artifacts';comparisons=[]
 for prefix,directory,gold,names in [('search',P/'artifacts',searchgold,['attachment.raw','goal.raw','metadata.raw','observations.raw','path_nodes.raw','path_pips.raw','result.raw']),('commit',P/'artifacts/commit',postgold,['canonical_reads.raw','control.raw','nets.raw','proposal_completion.raw','resources.raw','trees.raw'])]:
  for name in names:
   f=directory/name
   comparisons.append(dict(artifact=prefix+'/'+name,present=f.exists(),byte_match=f.exists() and sha(f)==sha(gold/name)))
 log=(P/'run.log').read_text();stages=[dict(name=n,operation=int(a),value=int(b),steady_ns=int(t)) for n,a,b,t in re.findall(r'STAGE name=(\S+) a=(\d+) b=(\d+) steady_ns=(\d+)',log)]
 complete=m['status']=='diagnostic_exited_requires_review' and m['returncode']==0
 execution=None
 if complete:
  rows=[]
  for line in (P/'stdout.log').read_text().splitlines():
   try:rows.append(json.loads(line))
   except ValueError:pass
  execution=next(v for v in rows if v.get('status')=='executed')
  for k,v in x['expected'].items():
   observed=(P/'artifacts/path_nodes.raw').stat().st_size//4 if k=='path_hops' else execution[k];assert observed==v,(k,observed,v)
  assert (P/'artifacts/path_nodes.raw').stat().st_size%4==0
  assert execution['authority_imports']==1 and execution['authority_reuploads']==0 and execution['verified_upload_bytes']==4482650920
  assert all(v['byte_match'] for v in comparisons)
  returned=[v for v in stages if v['name']=='kernel_wait_return'];assert len(returned)==43 and [v['operation'] for v in returned]==[3]+[7]*42
 else:
  assert m['returncode']!=0
  if m['status']=='bounded_diagnostic_not_completed':
   assert m['reason'] in ['predeclared_diagnostic_wall_bound','predeclared_diagnostic_memory_guard']
   if m['reason']=='predeclared_diagnostic_wall_bound':assert 1800<=m['elapsed_wall_seconds']<1830
   assert not set(x['original_jobs_untouched'])&{pid for pid,_ in m['observed_descendants']}
   for pid,birth in m['observed_descendants']:
    f=Path('/proc')/str(pid)/'stat';assert not f.exists() or f.read_text().split()[21]!=birth or f.read_text().split()[2]=='Z'
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'image_binding.json',P/'stdout.log',P/'run.log',P/'wait_observation_changes.json',parent,postgold.parent/'independent_audit.json',searchgold.parent.parent/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='two_phase_full_native_XRT_search_commit42queries13raw_match' if complete else 'two_phase_full_native_XRT_not_completed_partial_evidence_retained',completed=complete,comparisons=comparisons,execution=execution,terminal=m,last_stage=stages[-1] if stages else None,wait_returns=[v for v in stages if v['name']=='kernel_wait_return'],wait_exceptions=[v for v in stages if v['name']=='kernel_wait_exception'],source_sha256=refs,board_result=False,research_complete=False,adopted=False,scope='Exact new image binding, unchanged fullgraph/budgets and wait-observation-only host change. Complete shared-BO handoff accepted only with1proposal42queries and13raw parity. Partial outputs and waits do not establish device progress, deadlock, timeout cause, physical performance or adoption.')
 with (P/'independent_outcome_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(report['status'])
if __name__=='__main__':main()
