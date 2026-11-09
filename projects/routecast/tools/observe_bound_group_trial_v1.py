"""Bounded read-only observation of the original paired-trial process chain."""
import json,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_bound_group_refinement_v1_2026-10-20';C=R/'experiments/bound_group_refinement_launch_chain_v1_2026-10-20'
def process(pid,script):
 p=Path('/proc')/str(pid)
 try:
  args=(p/'cmdline').read_bytes().split(b'\0');identity=any(a.decode(errors='replace').endswith('/'+script) or a.decode(errors='replace')=='tools/'+script for a in args);stat=(p/'stat').read_text().rsplit(')',1)[1].split();status=(p/'status').read_text().splitlines();rss=next(int(s.split()[1]) for s in status if s.startswith('VmRSS:'))
  return dict(pid=pid,identity_matches=identity,state=stat[0],startticks=stat[19],rss_KiB=rss)
 except FileNotFoundError:return dict(pid=pid,present=False)
def last_event(path):
 if not path.exists():return dict(started=False)
 size=path.stat().st_size
 if not size:return dict(started=True,events_bytes=0,completed_groups_observed=0)
 chunk=65536
 with path.open('rb') as f:
  while True:
   begin=max(0,size-chunk);f.seek(begin);lines=f.read(size-begin).splitlines()
   if begin and lines:lines=lines[1:]
   for line in reversed(lines):
    try:e=json.loads(line)
    except (ValueError,UnicodeDecodeError):continue
    if isinstance(e,dict) and 'index' in e:return dict(started=True,events_bytes=size,completed_groups_observed=e['index']+1,last_status=e['status'])
   if begin==0 or chunk>=8*2**20:return dict(started=True,events_bytes=size,last_complete_event_unavailable_in_bounded_tail=True)
   chunk*=2
def main():
 state=json.loads((C/'state.json').read_text());rows=[]
 for name,pid,total in [('episode_01',3344768,8290),('episode_02',3344767,8326),('episode_03',3344766,8337)]:
  case=D/'w160'/name;arms={}
  for arm in ['off','on']:
   folder=case/arm;arms[arm]=dict(**last_event(folder/'events.jsonl'),audit_exists=(folder/'complete_event_audit.json').exists())
  rows.append(dict(case=name,scheduled_groups_per_arm=total,worker=process(pid,'run_bound_group_refinement_case_v1.py'),arms=arms))
 print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),chain=state,chain_process=process(3325290,'after_compact_cost_bound_trial_v1.py'),wrapper=process(3344762,'run_bound_group_refinement_trial_v1.py'),rows=rows,scope='Bounded live process/log observation only. Audit existence is not verified audit admission; no terminal quality or performance claim.'),indent=2))
if __name__=='__main__':main()
