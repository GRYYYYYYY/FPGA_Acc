"""Legacy-v-compact full group transcripts, failure preservation and context checks."""
import copy,json,hashlib
from pathlib import Path
from check_group_vacancy_proposal_v1 import fixture
from group_vacancy_proposal_v4 import Snapshot,propose
from group_vacancy_proposal_v3 import propose as zero_propose
from bound_enabled_group_graph_v1 import bind
from compact_target_raw_bounds_v1 import CompactReverseBounds
from reverse_raw_delay_bounds_v1 import ReverseBounds
R=Path(__file__).resolve().parents[1];D=R/'experiments/bound_enabled_group_proposal_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);runs=0;rejected=0
 for kwargs in ({},{'no_B_detour':True},{'shared_new_channel':True}):
  f,g,rc,slots,qs,old,new,crit,ledger=fixture(**kwargs);s=Snapshot(f,rc,slots,qs,old,ledger,crit,[1]*g.n,{}, {},0);before=copy.deepcopy((old,ledger,qs,crit));a=bind(g,ReverseBounds(g.offsets,g.dest,g.inc));b=bind(g,CompactReverseBounds(g.offsets,g.dest,g.inc))
  for limit in (1,2,3,10000):
   ca,ma=propose(s,a,limit);cb,mb=propose(s,b,limit);assert ca==cb and ma==mb;assert (old,ledger,qs,crit)==before;runs+=1
  # Existing zero provider behavior is unchanged except descriptive policy text.
  ca,ma=zero_propose(s,g);cb,mb=propose(s,g)
  if 'policy' in ma:ma['policy']=mb['policy']
  assert ca==cb and ma==mb
  changed=list(g.inc);changed[0]+=1
  try:bind(g,CompactReverseBounds(g.offsets,g.dest,changed))
  except ValueError:rejected+=1
  else:raise AssertionError('cost context mismatch accepted')
  before_bound=tuple(b.inc);g.inc[0]+=20;g.initial[0]+=1;assert b.inc==before_bound and b.initial[0]==0
 paths=[Path(__file__),R/'tools/bound_enabled_group_graph_v1.py',R/'tools/group_vacancy_proposal_v4.py',R/'tools/compact_target_raw_bounds_v1.py',R/'tools/reverse_raw_delay_bounds_v1.py']
 report=dict(status='QUALIFIED_BOUND_GROUP_LEGACY_COMPACT_TRANSCRIPT_PARITY_PASS',paired_group_runs=runs,wrong_context_rejections=rejected,caller_mutations_isolated=True,zero_provider_compatibility=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Small batch contracts only. Bound-v-zero search trajectory is deliberately not asserted equal. No full-cohort forecast or speed claim.')
 (D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
