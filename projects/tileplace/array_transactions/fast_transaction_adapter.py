import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'hbm_abi'))
from native_snapshot_adapter import NativeSnapshotEngine
from search_request import query
from compare_proposals import parse
class FastTransactionEngine(NativeSnapshotEngine):
 def propose_color(self,color,forbidden_ids=None):
  forbidden=forbidden_ids or set();self._send('QUERY\n'+query(self,color,True,forbidden))
  values=iter(self._line().split());eligible,proposals,accepted,rejected,kinds=[int(next(values)) for _ in range(5)]
  counts={next(values):int(next(values)) for _ in range(kinds)}
  rows=[]
  while True:
   row=self._line()
   if row=='END':break
   rows.append(row)
  actual=parse('\n'.join(rows))
  if len(actual)!=accepted or proposals-accepted!=rejected:raise RuntimeError('phase counts differ')
  selected=[]
  for identity,score in sorted(actual,key=lambda row:(row[1],row[0])):
   kind,units,trial=identity;t=self._make_transaction(kind,units,dict(trial))
   if t is None or t.transaction_id!=identity or t.score_q20!=score:raise RuntimeError('selected transaction differs')
   selected.append(t)
  self._verify_layout();self.checks.append({'color':color,'selected':len(actual),'forbidden':len(forbidden),'python_full_candidate_enumeration':False})
  return selected,{'color':color,'eligible_units':eligible,'proposals':proposals,'accepted':accepted,'rejected_conflicts':rejected,'forbidden_transactions':len(forbidden),'accepted_kinds':counts}
