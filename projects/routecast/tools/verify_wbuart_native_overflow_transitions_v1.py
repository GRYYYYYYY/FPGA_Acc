"""Per-iteration telescoping overflow and independent residual-bound arithmetic."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_native_overflow_transitions_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());horizon=E/'wbuart_native_iteration_horizon_v1_2026-10-20/verification.json';h=read(horizon);workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');graphs={};rows=[]
 for row in v['rows']:
  s=read(next(c['specification'] for c in workflow['comparisons'] if c['case']==row['case']));g=read(s['endpoint'])['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('capacity')) for _,e in ET.iterparse(g) if e.tag=='node' and e.get('capacity') is not None]
  caps=graphs[g];trajectory=next(r for r in h['rows'] if (r['case'],r['reference'])==(row['case'],row['reference']));before=trajectory['stages'][0]['ledger'];overflow=lambda ledger:sum(max(0,c-caps[int(n)]) for n,c in ledger.items());previous=overflow(before);deltas=Counter();count=0;positive_later=0;proved_later=0
  for line in Path(row['payload']).read_text().splitlines():
   e=json.loads(line);assert e['native_overflow_delta_lower_bound']<=e['native_overflow_delta_upper_bound'];deltas[e['iteration']]+=e['NET_owner_overflow_delta'];count+=1
   if e['iteration']>=2:positive_later+=e['NET_owner_overflow_delta']>0;proved_later+=e['native_overflow_delta_lower_bound']>0
  for stage in trajectory['stages']:
   if stage['tag']!='iteration_end_after_local_opins':continue
   current=overflow(stage['ledger']);assert current-previous==deltas[stage['iteration']];previous=current
  assert count==row['summary']['events'];rows.append({'case':row['case'],'reference':row['reference'],'events':count,'positive_NET_owner_overflow_changes_after_first_iteration':positive_later,'provably_positive_native_overflow_changes_after_first_iteration':proved_later,'all_iteration_deltas_telescope_to_independent_checkpoint_ledgers':True})
 fixtures=0
 for cap in range(1,7):
  for c in range(9):
   for change in [-1,1]:
    if c+change<0:continue
    values=[max(0,c+x+change-cap)-max(0,c+x-cap) for x in range(cap+c+4)];low,high=((int(c>=cap),1) if change==1 else (-1,-int(c>cap)));assert (min(values),max(values))==(low,high);fixtures+=1
 assert len(rows)==18 and all(r['positive_NET_owner_overflow_changes_after_first_iteration']>0 and r['provably_positive_native_overflow_changes_after_first_iteration']>0 for r in rows)
 (D/'independent_telescoping_verification_v1.json').write_text(json.dumps({'status':'ALL18_ITERATION_OVERFLOW_TELESCOPES_AND_RESIDUAL_BOUND_FIXTURES_PASS','rows':rows,'bound_fixtures':fixtures,'bindings':{str(p):sha(p),str(horizon):sha(horizon),str(Path(__file__)):sha(__file__)},'scope':'Independent checkpoint-ledger telescoping and exhaustive bounded residual arithmetic, not independent per-event trace/parser replay. Native lower bounds assume non-NET reservations stable during each NET call as source/trace semantics; unknown residuals remain intervals.'},indent=2)+'\n');print('ALL18_ITERATION_OVERFLOW_TELESCOPES_AND_RESIDUAL_BOUND_FIXTURES_PASS',fixtures)
if __name__=='__main__':main()
