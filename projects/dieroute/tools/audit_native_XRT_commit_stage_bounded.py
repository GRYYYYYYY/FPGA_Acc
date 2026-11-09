"""Check terminal logging-only fullgraph diagnostic and independent search parity."""
import hashlib,json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_identity_XRT_commit_stage_diagnostic_20261015'
def main():
 refs={}
 def sha(f):
  f=str(Path(f).resolve())
  if f not in refs:
   h=hashlib.sha256()
   with open(f,'rb') as v:
    for b in iter(lambda:v.read(1048576),b''):h.update(b)
   refs[f]=h.hexdigest()
  return refs[f]
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert x['maximum_probe_wall_seconds']==1800 and m['status']=='bounded_diagnostic_not_completed' and m['reason']=='predeclared_diagnostic_wall_bound'
 assert 1800<=m['elapsed_wall_seconds']<1830 and m['returncode']!=0
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 initial=json.loads((R/'work/native_XRT_first_commit_wait_observation_20261015/independent_audit.json').read_text());root=Path(f"/proc/{m['child_pid']}/stat");assert not root.exists() or root.read_text().split()[21]!=initial['observed_host_start_ticks']
 for pid,birth in m['observed_descendants']:
  f=Path(f'/proc/{pid}/stat');assert not f.exists() or f.read_text().split()[21]!=birth or f.read_text().split()[2]=='Z'
 assert not set(pid for pid,_ in m['observed_descendants'])&set(x['original_jobs_untouched']);assert all(Path(f'/proc/{pid}').exists() for pid in x['original_jobs_untouched'])
 old=R/'work/native_identity_higher_g_xrt_pipeline_20261015/artifacts';gold=R/'work/native_policy_identity_ordering_cpu_20261015/identity_higher_g/artifacts';compared=[]
 for name in ['result.raw','metadata.raw','goal.raw','observations.raw','attachment.raw','path_nodes.raw','path_pips.raw']:
  f=P/'artifacts'/name;assert sha(f)==sha(old/name)==sha(gold/name),name;compared.append(name)
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes());assert result[:2]==(0,43) and result[5]==256
 log=(P/'run.log').read_text();stages=[dict(name=n,a=int(a),b=int(b),steady_ns=int(t)) for n,a,b,t in re.findall(r'STAGE name=(\S+) a=(\d+) b=(\d+) steady_ns=(\d+)',log)]
 assert stages[-1]['name']=='kernel_wait_begin' and stages[-1]['a']==3 and not any(v['name']=='kernel_wait_complete' for v in stages)
 assert [v['a'] for v in stages if v['name']=='commit_BO_allocate_end']==[0,4,5,6,7,14,15,16] and [v['a'] for v in stages if v['name']=='commit_BO_zero_sync_end']==[0,4,5,6,7,14,15,16]
 names=[v['name'] for v in stages];assert all(v in names for v in ['reads_sync_end','branch_sync_end','paths_sync_end','command_sync_end','kernel_enqueue_returned'])
 assert not (P/'artifacts/commit').exists() and 'native commit op=' not in log
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.log',P/'stdout.log',P/'bounded_stage_outcome.json',R/'work/native_XRT_first_commit_wait_observation_20261015/independent_audit.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='second_fullgraph_search7raw_match_first_proposal_wait_not_completed_within1800s',guard_seconds=1800,observed_wall_seconds=m['elapsed_wall_seconds'],search_raw_comparisons=compared,last_stage=stages[-1],completed_commit_BO_allocations=8,first_proposal_enqueue_API_returned=True,source_sha256=refs,scope='Independent terminal review of logging-only run: fullgraph search found43/256obs and7raw parity reproduce. Allpreparation syncs returned, firstproposal host wait did not return before frozen guard. Original4jobs remain, own new descendants ended. No device-side progress/deadlock/cause, commit success/rejection, performance or physical claim.',board_result=False,research_complete=False)
 with (P/'independent_bounded_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(report['status'])
if __name__=='__main__':main()
