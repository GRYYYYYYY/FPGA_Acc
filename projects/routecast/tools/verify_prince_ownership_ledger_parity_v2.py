"""All cohort routes, resident observations and readiness decisions unchanged."""
import json
from pre_route_endpoints import sha
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_ownership_ledger_trial_v2_2026-10-20';OLD=R/'experiments/prince_owned_ready_trial_v1_2026-10-20'
def main():
 p=D/'verification.json';v=json.loads(p.read_text());oldp=OLD/'verification.json';prior={x['case']:x for x in json.loads(oldp.read_text())['rows']};bindings={str(p):sha(p),str(oldp):sha(oldp),str(__file__):sha(__file__)};observations=payloads=0
 for row in v['rows']:
  case=row['case'];a=D/case;b=OLD/case;assert row['callback_sequence_complete'] and row['nonclock_iteration_summaries_equal'] and row['terminal_physical_sequences_equal']
  for name,cols in [('callback.tsv',11),('callback.tsv.owners.tsv',10),('callback.tsv.ready.tsv',8)]:
   ap=a/name;bp=b/name;assert sha(ap)==row['files'][str(ap)] and sha(bp)==prior[case]['files'][str(bp)];assert [s.split()[:cols] for s in ap.read_text().splitlines()]==[s.split()[:cols] for s in bp.read_text().splitlines()];bindings[str(ap)]=sha(ap);bindings[str(bp)]=sha(bp)
   if name=='callback.tsv':observations+=len(ap.read_text().splitlines())
  if case.endswith('/capture'):
   for dirname in ['boundary','owners']:
    for ap in (a/dirname).glob('*.bin'):
     bp=b/dirname/ap.name;h=sha(ap);assert h==row['files'][str(ap)]==sha(bp)==prior[case]['files'][str(bp)];bindings[str(ap)]=h;bindings[str(bp)]=h;payloads+=1
 assert observations==454 and payloads==681;out=D/'observation_parity_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL18_OWNERSHIP_LEDGER_PARITY_PASS',observations=observations,equal_binary_payloads=payloads,bindings=bindings),indent=2)+'\n');print('CONNECTION_OBSERVATION_PARITY_PASS',observations,payloads)
if __name__=='__main__':main()
